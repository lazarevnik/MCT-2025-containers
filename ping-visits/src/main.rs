#[actix_web::main]
async fn main() -> anyhow::Result<()> {
    dotenv::dotenv().ok();
    ping_visits::run_server().await
}
