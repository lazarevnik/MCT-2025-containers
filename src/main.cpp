#include <string>
#include <fstream>
#include <restbed>
#include <streambuf>
#include <set>
#include <iostream>
#include <libpq-fe.h>

using namespace std;
using namespace restbed;

long long visits = 0;
set<string> visitors_ip;
PGconn* db_connection = nullptr;

void init_database()
{
    const char* db_info = "host=db "
                          "port=5432 "
                          "dbname=db "
                          "user=user "
                          "password=password";
    db_connection = PQconnectdb(db_info);
    if (PQstatus(db_connection) != CONNECTION_OK) {
        cerr << "Database connection failed: "
             << PQerrorMessage(db_connection) << endl;
        PQfinish(db_connection);
        db_connection = nullptr;
    }
}

void ping_handler(const shared_ptr<Session> session)
{
    const string origin_ip = session->get_origin();

    if (visitors_ip.find(origin_ip) == visitors_ip.end()) {
        if (!db_connection) {
            session->close(INTERNAL_SERVER_ERROR, "Datatbase connection error");
            return;
        }
        visitors_ip.insert(origin_ip);

        const char *query = "INSERT INTO visitors (ip) VALUES ($1)";
        const char *paramValues[1];
        paramValues[0] = origin_ip.c_str();
        PGresult* result = PQexecParams(db_connection, query, 1, NULL,
                                        paramValues, NULL, NULL, 1);

        if (PQresultStatus(result) != PGRES_COMMAND_OK) {
                session->close(INTERNAL_SERVER_ERROR, "Insert query failed");
                PQclear(result);
                return;
        }
    }

    visits += 1;
    const string body = "pong";
    const multimap<string, string> headers {
        { "Content-Type", "text/html" },
        { "Content-Length", ::to_string(body.length()) }
    };

    session->close(OK, body, headers);
}

void visits_handler(const shared_ptr<Session> session)
{
    const string body = to_string(visits);
    const multimap<string, string> headers {
        { "Content-Type", "text/html" },
        { "Content-Length", ::to_string(body.length()) }
    };

    session->close(OK, body, headers);
}

void visitors_handler(const shared_ptr<Session> session)
{
    const char* query = "SELECT id, ip FROM visitors ORDER BY id";
    PGresult* result = PQexec(db_connection, query);

    if (PQresultStatus(result) != PGRES_TUPLES_OK) {
        session->close(INTERNAL_SERVER_ERROR, "SELECT query failed");
        PQclear(result);
        return;
    }

    string body;
    int row_count = PQntuples(result);
    for (int i = 0; i < row_count; ++i) {
        body += "\"ip\":\"" + string(PQgetvalue(result, i, 1)) + "\n";
    }

    const multimap<string, string> headers {
        { "Content-Type", "text/html" },
        { "Content-Length", ::to_string(body.length()) }
    };

    PQclear(result);

    session->close(OK, body, headers);
}

void root_handler(const shared_ptr<Session> session)
{
    session->close(OK, "", {{"Connection", "Close"}});
}

void get_method_handler(const shared_ptr<Session> session)
{
    const auto request = session->get_request();
    const string path = request->get_path_parameter("request");

    if (path == "ping") {
        ping_handler(session);
    } else if (path == "visits") {
        visits_handler(session);
    } else if (path == "visitors") {
        visitors_handler(session);
    }

    session->close(NOT_FOUND);
}

int main(const int, const char**) {
    init_database();

    auto root_resource = make_shared<Resource>();
    root_resource->set_path("/");
    root_resource->set_method_handler("GET", root_handler);

    auto resource = make_shared<Resource>();
    resource->set_path("/{request: [a-z]*}");
    resource->set_method_handler("GET", get_method_handler);

    auto settings = make_shared< Settings >();
    settings->set_port(5000);
    settings->set_default_header("Connection", "close");

    Service service;
    service.publish(root_resource);
    service.publish(resource);
    service.start(settings);

    if (db_connection) {
        PQfinish(db_connection);
    }

    return EXIT_SUCCESS;
}
