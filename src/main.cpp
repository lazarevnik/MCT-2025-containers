#include <string>
#include <memory>
#include <cstdlib>
#include <fstream>
#include <restbed>
#include <streambuf>
#include <set>
#include <libpq-fe.h>
#include <iostream>

using namespace std;
using namespace restbed;

long long visits = 0;
set<string> visitors_ip;
PGconn* db_connection = nullptr;

void init_database()
{
    const char* db_info = "host=postgres "
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

void get_method_handler(const shared_ptr<Session> session)
{
    const auto request = session->get_request();
    const string request_param = request->get_path_parameter("request");
    if (request_param == "ping") {
        const string origin_ip = session->get_origin();

        if (visitors_ip.find(origin_ip) == visitors_ip.end()) {
            if (!db_connection) {
                session->close(INTERNAL_SERVER_ERROR, "Datatbase connection error");
                return;
            }
            visitors_ip.insert(origin_ip);
	    /*
            const char *query = "INSERT INTO visitors (ip) VALUES ($1)";
	    const char *paramValues[1];
	    paramValues[0] = origin_ip.c_str();
            PGresult* result = PQexecParams(db_connection,
                                            query,
                                            1,
                                            NULL,
                                            paramValues,
                                            NULL,
                                            NULL,
                                            1);
					    */
	    const char* escaped_ip = PQescapeLiteral(db_connection, origin_ip.c_str(), origin_ip.size());
	        
	    std::string query = "INSERT INTO visitors (ip) VALUES (";
	    query += escaped_ip;
	    query += ") ON CONFLICT (ip) DO UPDATE SET created_at = CURRENT_TIMESTAMP";
			    
	    PGresult* result = PQexec(db_connection, query.c_str());
	    if (PQresultStatus(result) != PGRES_COMMAND_OK) {
                session->close(INTERNAL_SERVER_ERROR, "Insert query failed");
                //PQclear(result);
		fprintf(stderr, "SELECT failed: %s", PQerrorMessage(db_connection));
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
    } else if (request_param == "visits") {
        const string body = to_string(visits);
        const multimap< string, string > headers {
            { "Content-Type", "text/html" },
            { "Content-Length", ::to_string(body.length()) }
        };

        session->close(OK, body, headers);
    } else if (request_param == "visitors") {
        string body;

	/*
        for (const auto &ip : visitors_ip) {
            body += ip;
            body += '\n';
        }

        const multimap<string, string> headers {
            { "Content-Type", "text/html" },
            { "Content-Length", ::to_string(body.length()) }
        };
	*/

	const char* query = "SELECT id, ip FROM visitors ORDER BY id";
	    PGresult* result = PQexec(db_connection, query);
	        
	    if (PQresultStatus(result) != PGRES_TUPLES_OK) {
		session->close(INTERNAL_SERVER_ERROR, "Database query failed");
		fprintf(stderr, "SELECT failed: %s", PQerrorMessage(db_connection));
		PQclear(result);
		return;
	    }
	string json = "{\"users\":[";
	    int row_count = PQntuples(result);
	        
	        for (int i = 0; i < row_count; i++) {
			        if (i > 0) json += ",";
				        json += "{";
					        json += "\"id\":" + string(PQgetvalue(result, i, 0)) + ",";
						        json += "\"ip\":\"" + string(PQgetvalue(result, i, 1)) + "\",";
								        json += "}";
									    }
		    json += "]}";
		        
		        multimap<string, string> headers = {
				        {"Content-Type", "application/json"},
					        {"Content-Length", to_string(json.size())}
					    };
			    
			    PQclear(result);

        session->close(OK, json, headers);
    } else {
        session->close(NOT_FOUND);
    }
}

int main(const int, const char**) {
    init_database();

    auto resource = make_shared<Resource>();
    resource->set_path("/{request: [a-z]*}");
    resource->set_method_handler("GET", get_method_handler);

    auto settings = make_shared< Settings >();
    settings->set_port(5000);
    settings->set_default_header("Connection", "close");

    Service service; service.publish(resource);
    service.start(settings);

    return EXIT_SUCCESS;
}

