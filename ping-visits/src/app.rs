use std::env;

use actix_web::{App, HttpRequest, HttpResponse, HttpServer, Responder, web};
use anyhow::Context;
use redis::{AsyncCommands, Client, RedisResult};
use sqlx::{PgPool, postgres::PgPoolOptions};

#[derive(Clone)]
pub struct AppState {
    db: PgPool,
    redis: redis::Client,
}

impl AppState {
    const REDIS_NVISITS_KEY: &'static str = "nvisits";
    const REDIS_CACHE_TIMEOUT_SEC: u64 = 600;

    pub fn new(db: PgPool, redis: Client) -> Self {
        Self { db, redis }
    }

    pub async fn from_env() -> anyhow::Result<Self> {
        let db_url = env::var("DATABASE_URL").context("`DATABASE_URL` must be set")?;
        let redis_url = env::var("REDIS_URL").unwrap_or("redis://redis:6379".to_owned());

        let pool = PgPoolOptions::new()
            .max_connections(20)
            .connect(&db_url)
            .await
            .context("failed to connect to `DATABASE_URL`")?;
        let redis = Client::open(redis_url).context("failed to connect to Redis")?;

        Ok(Self::new(pool, redis))
    }

    async fn redis_con(&self) -> RedisResult<redis::aio::MultiplexedConnection> {
        self.redis.get_multiplexed_async_connection().await
    }

    pub async fn redis_invalidate(&self) {
        if let Ok(mut con) = self.redis_con().await {
            if let Err(e) = con.del::<_, i64>(Self::REDIS_NVISITS_KEY).await {
                eprintln!("Redis: failed to delete cache: {e}");
            }
        }
    }

    pub async fn redis_set(&self, count: i64) {
        if let Ok(mut con) = self.redis_con().await {
            let _: Result<(), _> = con
                .set_ex(
                    Self::REDIS_NVISITS_KEY,
                    count,
                    Self::REDIS_CACHE_TIMEOUT_SEC,
                )
                .await;
        }
    }

    pub async fn redis_get(&self) -> Option<i64> {
        let mut con = self.redis_con().await.ok()?;
        let count: Result<Option<i64>, _> = con.get(Self::REDIS_NVISITS_KEY).await;
        count.ok()?
    }

    pub async fn visits_from_db(&self) -> HttpResponse {
        match sqlx::query_scalar!("select count(*) from visits")
            .fetch_one(&self.db)
            .await
        {
            Ok(Some(count)) => {
                self.redis_set(count).await;
                HttpResponse::Ok().body(count.to_string())
            }
            Ok(None) => HttpResponse::Ok().body("0"),
            Err(e) => {
                eprintln!("failed to select count(*) from visits: {e}");
                HttpResponse::InternalServerError().finish()
            }
        }
    }

    pub async fn insert_ip(&self, ip: String) -> Result<(), sqlx::Error> {
        let _ = sqlx::query!("insert into visits (ip_address) values ($1)", ip)
            .execute(&self.db)
            .await?;

        self.redis_invalidate().await;
        Ok(())
    }
}

pub async fn ping(state: web::Data<AppState>, req: HttpRequest) -> HttpResponse {
    static RESPONSE_BODY: &'static str = "pong";

    let ip = req
        .peer_addr()
        .map_or("unknown".to_owned(), |addr| addr.ip().to_string());

    if let Err(e) = state.insert_ip(ip).await {
        eprintln!("failed to insert ip: {e}");
        HttpResponse::InternalServerError().finish()
    } else {
        HttpResponse::Ok().body(RESPONSE_BODY)
    }
}

pub async fn visits(state: web::Data<AppState>) -> HttpResponse {
    if let Some(cached_count) = state.redis_get().await {
        HttpResponse::Ok().body(cached_count.to_string())
    } else {
        state.visits_from_db().await
    }
}

pub async fn index() -> impl Responder {
    "Hello, Docker!"
}

pub async fn run_server() -> anyhow::Result<()> {
    let state = web::Data::new(AppState::from_env().await?);

    let addr = std::net::SocketAddr::from(([0, 0, 0, 0], 80));
    println!("HTTP server listens on {addr}");

    Ok(HttpServer::new(move || {
        App::new()
            .app_data(state.clone())
            .route("/", web::get().to(index))
            .route("/visits", web::get().to(visits))
            .route("/ping", web::get().to(ping))
    })
    .bind(addr)?
    .run()
    .await?)
}
