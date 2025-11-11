use std::env;

#[actix_web::main]
async fn main() -> anyhow::Result<()> {
    dotenv::dotenv().ok();

    if env::var("DEV").is_ok() {
        ping_visits::run_dev_server().await
    } else {
        ping_visits::run_server().await
    }
}
