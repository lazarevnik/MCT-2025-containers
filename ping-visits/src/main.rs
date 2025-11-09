use std::env;

use actix_web::{App, HttpRequest, HttpResponse, HttpServer, Responder, web};
use anyhow::Context;
use sqlx::{PgPool, postgres::PgPoolOptions};

#[derive(Clone)]
struct AppState {
    db: PgPool,
}

impl AppState {
    pub fn new(db: PgPool) -> Self {
        Self { db }
    }
}

async fn ping(state: web::Data<AppState>, req: HttpRequest) -> HttpResponse {
    static RESPONSE_BODY: &'static str = "pong";

    let ip = req
        .peer_addr()
        .map_or("unknown".to_owned(), |addr| addr.ip().to_string());

    if let Err(e) = sqlx::query!("insert into visits (ip_address) values ($1)", ip)
        .execute(&state.db)
        .await
    {
        eprintln!("failed to insert ip: {e}");
        HttpResponse::InternalServerError().finish()
    } else {
        HttpResponse::Ok().body(RESPONSE_BODY)
    }
}

async fn visits(state: web::Data<AppState>) -> HttpResponse {
    match sqlx::query_scalar!("select count(*) from visits")
        .fetch_one(&state.db)
        .await
    {
        Ok(Some(count)) => HttpResponse::Ok().body(count.to_string()),
        Ok(None) => HttpResponse::Ok().body("0"),
        Err(e) => {
            eprintln!("failed to select count(*) from visits: {e}");
            HttpResponse::InternalServerError().finish()
        }
    }
}

async fn index() -> impl Responder {
    "Hello, Docker!"
}

#[actix_web::main]
async fn main() -> anyhow::Result<()> {
    dotenv::dotenv().ok();

    let db_url = env::var("DATABASE_URL").context("`DATABASE_URL` must be set")?;

    let pool = PgPoolOptions::new()
        .max_connections(20)
        .connect(&db_url)
        .await
        .context("failed to connect to `DATABASE_URL`")?;

    let state = web::Data::new(AppState::new(pool));

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
