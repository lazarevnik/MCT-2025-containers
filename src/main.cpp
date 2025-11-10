#include <string>
#include <memory>
#include <cstdlib>
#include <fstream>
#include <restbed>
#include <streambuf>
#include <set>

using namespace std;
using namespace restbed;

long long visits = 0;
set<string> visitors_ip;

void get_method_handler(const shared_ptr<Session> session)
{
	const auto request = session->get_request();
	const string request_param = request->get_path_parameter("request");
	if (request_param == "ping") {
		visitors_ip.insert(session->get_origin());
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

		for (const auto &ip : visitors_ip) {
			body += ip;
			body += '\n';
		}

		const multimap<string, string> headers {
			{ "Content-Type", "text/html" },
			{ "Content-Length", ::to_string(body.length()) }
		};

		session->close(OK, body, headers);
	} else {
		session->close(NOT_FOUND);
	}
}

int main(const int, const char**) {
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

