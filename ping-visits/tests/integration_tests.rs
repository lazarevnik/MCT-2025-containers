use std::env;

use actix_web::{App, test, web};
use anyhow::Context;
use ping_visits::{AppState, ping, visits};
use rand::Rng;

use sqlx::PgPool;

#[actix_web::test]
async fn test_ping() -> anyhow::Result<()> {
    let state = web::Data::new(AppState::from_env().await?);

    let app = test::init_service(
        App::new()
            .app_data(state.clone())
            .route("/ping", web::get().to(ping)),
    )
    .await;

    let req = test::TestRequest::get().uri("/ping").to_request();
    let resp = test::call_and_read_body(&app, req).await;

    assert_eq!(resp, "pong");

    Ok(())
}

#[actix_web::test]
async fn test_visists_healhty() -> anyhow::Result<()> {
    let state = web::Data::new(AppState::from_env().await?);

    let app = test::init_service(
        App::new()
            .app_data(state.clone())
            .route("/visits", web::get().to(visits)),
    )
    .await;

    let req = test::TestRequest::get().uri("/visits").to_request();
    let resp = test::call_service(&app, req).await;

    assert!(resp.status().is_success());

    Ok(())
}

#[tokio::test]
async fn test_redis_cache_cycle() -> anyhow::Result<()> {
    let state = AppState::from_env().await?;

    state.redis_set(42).await;
    assert_eq!(state.redis_get().await, Some(42));

    state.redis_invalidate().await;
    assert_eq!(state.redis_get().await, None);

    Ok(())
}

#[tokio::test]
async fn test_visits_increment_after_pings() -> anyhow::Result<()> {
    const BASE_URL: &str = "http://localhost:8080";

    std::thread::spawn(|| {
        let sys = actix_web::rt::System::new();
        sys.block_on(async {
            ping_visits::run_server().await.unwrap();
        });
    });

    // Wait for server to start.
    tokio::time::sleep(std::time::Duration::from_secs(3)).await;

    let resp = reqwest::get(format!("{}/visits", BASE_URL))
        .await
        .context("failed to request /visits")?;

    assert!(resp.status().is_success(), "GET /visits failed");

    let body = resp.text().await.context("failed to read /visits body")?;
    let nvisits: i64 = body.trim().parse().unwrap_or(0);

    let mut rng = rand::rng();
    let n_pings = rng.random_range(5..10);

    for _ in 0..n_pings {
        let resp = reqwest::get(format!("{}/ping", BASE_URL))
            .await
            .context("failed to send /ping")?;

        assert!(resp.status().is_success(), "/ping failed");

        let text = resp.text().await.unwrap_or_default();
        assert_eq!(text, "pong", "unexpected /ping response");
    }

    let resp = reqwest::get(format!("{}/visits", BASE_URL))
        .await
        .context("failed to send request to /visits after pings")?;

    assert!(resp.status().is_success());

    let body = resp.text().await.expect("failed to read /visits body");
    let nvisits_after_pings: i64 = body.trim().parse().unwrap_or(0);

    assert!(
        nvisits_after_pings - nvisits == n_pings,
        "expected visits to increase by {}, but got: {} -> {}",
        n_pings,
        nvisits,
        nvisits_after_pings
    );

    Ok(())
}

#[tokio::test]
async fn test_visits_without_redis() -> anyhow::Result<()> {
    let db_url = env::var("DATABASE_URL").context("DATABASE_URL must be set")?;

    let pool = PgPool::connect(&db_url)
        .await
        .context("failed to connect to database")?;

    // Invalid Redis port.
    let redis = redis::Client::open("redis://127.0.0.1:6390").unwrap();
    let state = AppState::new(pool, redis);

    let resp = state.visits_from_db().await;
    assert!(resp.status().is_success());

    Ok(())
}

#[tokio::test]
async fn test_redis_invalidate_fails_gracefully() -> anyhow::Result<()> {
    let state = AppState::from_env().await?;

    state.redis_invalidate().await;

    Ok(())
}
