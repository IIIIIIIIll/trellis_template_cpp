#ifndef TOOLS_STUBS_STUBS_HPP
#define TOOLS_STUBS_STUBS_HPP

// tools/stubs/stubs.hpp — compile-stub prelude for tools/check_snippets.py.
//
// The snippet harness prepends this header (plus a #line directive) to every
// fenced ```cpp example before running g++ -Wall -Wextra -fsyntax-only
// (-std=c++14 baseline; fences annotated // C++17 / // C++20 compile at
// -std=c++17 / -std=c++20), so
// guideline examples can use the standard library freely and name the
// invented types each guide uses (Session, Task, JoinOptions, ...) without
// carrying their definitions inline.
//
// Two halves:
//   1. a common std prelude — every guide's examples lean on the same core
//      headers; including them here keeps the examples focused on the rule
//      being shown. C++17- and C++20-only headers are guarded so the same
//      prelude works under -std=c++14, -std=c++17, and -std=c++20.
//   2. stub declarations for invented names — declared, not defined where the
//      docs define them; keep bodies trivial. Stubs must never collide with a
//      name any doc fence defines (the harness compiles such fences per
//      Wrong/Right section, and a stub clash would break them).
//
// tools/stubs/include/ holds standalone stub headers the examples reference
// (tl/expected.hpp, result.h), surfaced via -isystem; tools/stubs/per-doc/
// holds per-doc additions for names one guide spells differently.

// --- 1. common std prelude ---------------------------------------------------

#include <algorithm>
#include <array>
#include <atomic>
#include <cassert>
#include <cctype>
#include <cerrno>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <exception>
#include <filesystem>
#include <fstream>
#include <functional>
#include <future>
#include <initializer_list>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <limits>
#include <list>
#include <map>
#include <memory>
#include <mutex>
#include <new>
#include <numeric>
#include <ostream>
#include <queue>
#include <random>
#include <set>
#include <shared_mutex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <system_error>
#include <thread>
#include <tuple>
#include <type_traits>
#include <typeinfo>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <unistd.h>
#include <vector>

// C++17-only headers: libstdc++ tolerates including them at C++14 (contents
// guarded out) but libc++ hard-errors pre-17, so gate them like the C++20
// block below.
#if __cplusplus >= 201703L
#include <optional>
#include <string_view>
#include <variant>
#endif

#if __cplusplus >= 202002L
#include <bit>
#include <compare>
#include <concepts>
#include <coroutine>
#include <numbers>
#include <ranges>
#include <semaphore>
#include <span>
#include <stop_token>
#include <version>
#endif

// --- 2. stub declarations for invented names ---------------------------------
// Grouped by the doc that needs each name.
//
// Declarations naming C++17-only standard types (std::string_view,
// std::optional, std::variant) sit behind `#if __cplusplus >= 201703L`: those
// names do not exist at the C++14 baseline, and fences relying on such stubs
// carry a `// C++17` fence marker. Inline namespace-scope variables stay
// unguarded (warning-only at C++14; the gate has no -Werror).

// headers-and-dependencies.md + static-analysis.md (QUAL split)
enum class Mode { kFast, kSafe, kRaw };

struct Logger {
    virtual ~Logger() = default;
};
inline Logger g_logger;          // QUAL-48 wrong section references the name
struct Registry {
    explicit Registry(Logger*) {}
};
struct Config {};

struct Base {                    // QUAL slicing example
    virtual ~Base() = default;
};
struct HttpHandler : Base {};

enum class EventKind { kHttp, kTimer };
struct Event {
    virtual ~Event() = default;
    EventKind kind_ = EventKind::kHttp;
    EventKind kind() const { return kind_; }
};
struct HttpEvent : Event {};
struct TimerEvent : Event {};
inline Event ev;                 // QUAL-50 dispatch fragment
inline void handle_http(const HttpEvent&) {}
inline void handle_timer(const TimerEvent&) {}

// templates-and-generics.md
namespace detail {  // TPL-23 Right section: qualified dependent helper call
template <typename It>
std::size_t count_matches(It, It);
}  // namespace detail
struct User {  // TPL-24 / TEST-32 examples
    explicit User(const char*) {}
    std::string name() const { return "ada"; }
};

// classes-and-hierarchies.md
struct Conn {};
struct Point {
    int x, y;
};
class Transport {
public:
    virtual ~Transport() = default;
};
struct Session {
    Session() = default;
    explicit Session(Config) {}
    void initialize(Config) {}
    bool init(Config) { return false; }  // ERR-12 two-stage spelling
};
inline Config config;  // CLS-22 two-stage-construction fragment references it
using Bytes = std::vector<char>;       // CLS-72 Codec interface
#if __cplusplus >= 201703L
using BytesView = std::string_view;    // CLS-72 Codec interface
#endif

// concurrency.md
struct Request {};
inline void send_reply(const Request&) {}
struct Device {
    void sample() {}
};
struct Listener {
    virtual ~Listener() = default;
    virtual void on_event(const Event&) {}
};
inline std::mutex listenersMutex_;
inline std::mutex queueMutex_;   // CONC-19 guard spellings
inline std::mutex m1;            // CONC-19 guard spellings
template <typename T>
class ThreadSafeQueue {
public:
    T pop() { return T(); }
    void push(T) {}
};
struct Job {};
inline void process(const Job&) {}
struct Chunk {};
inline Chunk chunk;
inline Chunk compress_chunk(Chunk);

#if __cplusplus >= 202002L
inline void request_shutdown(std::stop_token) {}  // C++20 poll_device example
#endif

// error-contracts.md + error-propagation.md
struct Item {};
struct Key {};
struct Value {};
struct Map {
    Item at(Key) const { return Item{}; }
#if __cplusplus >= 201703L
    std::optional<Item> lookup(Key) const { return std::nullopt; }
#endif
};
struct Table {
    Value& operator[](int) { static Value v; return v; }
};
constexpr int FAIL = -1;
inline int table_index(Key) { return 0; }
inline Key key;        // ERR-8 wrong fragment calls table_index(key)
inline Config cfg;     // ERR-12 fragment
struct ValidationError : std::exception {
    int code() const { return 0; }
};
inline void run() {}
inline void log(int) {}
inline void log(const char*) {}
struct LegacyFile {
    void close() {}
};
inline LegacyFile legacy_file;  // ERR-46 best-effort cleanup
enum {                          // ERR-43 module-edge status codes
    MYLIB_OK = 0,
    MYLIB_OUT_OF_MEMORY,
    MYLIB_PARSE_ERROR,
    MYLIB_ERROR,
    MYLIB_UNKNOWN
};
struct ParseError : std::exception {};
struct MylibDoc;  // opaque across the C ABI
#if __cplusplus >= 201703L
inline MylibDoc* parse_doc(std::string_view);
#endif
inline MylibDoc* release_to_c(MylibDoc*);
inline void set_last_error(const char*);
struct Handler {
    void on_event(const Event&) {}
};
inline std::size_t size();  // ERR-38 ambient size() in the wrong example
struct TransientError : std::exception {};
inline void schedule_retry(int) {}
inline int attempt_ = 0;      // ERR-47 retry counter
inline std::string path;      // ERR-15 usage fragment
inline std::string path_;     // ERR-51 annotation message
inline void use(const Config&) {}
inline void use(const int&) {}  // MEM-39 dangling-reference fragment
inline void save_document() {}  // ERR-47 fragment context
inline void load() {}           // ERR-51 fragment context
#define LOG(severity) std::cerr  // glog-style spelling in ERR-47

// functions-and-interfaces.md
struct Stats {};
inline std::vector<User> users_;  // FN-19 sink examples
struct Token {};
inline constexpr std::size_t PREFIX_LEN = 4;
struct AST {};
struct Error {};
struct Entry {};
struct Record {};
struct Message {
    std::string key;
    std::string value;
    std::string serialize() const { return {}; }
};
inline Message decode(const uint8_t*, std::size_t) { return {}; }
inline bool valid(const Message&) { return true; }
inline int g_errors = 0;
inline std::map<std::string, std::string> g_cache;
inline void send(const std::string&) {}
inline void cache_store(const std::string&, const std::string&) {}
inline std::string serialize(const Message&) { return {}; }
class TaskQueue {
public:
    template <typename F>
    void push(F&&) {}
};
inline uint16_t port_count() { return 0; }
inline uint16_t scale() { return 0; }
inline int attempts = 0;  // FN-53 magic-number example
struct Account {};
struct Amount { double value = 0; };
struct Ledger {};
struct Rect {
    int width = 0;
    int height = 0;
};

// memory-discipline.md
inline bool parse(std::FILE*);                           // MEM-1 wrong example
inline bool parse(std::ifstream&);                       // MEM-1 right example
#if __cplusplus >= 201703L
inline std::string normalize(std::string_view);          // MEM-38 wrong example
inline std::string_view extract_host(const std::string&);
#endif
inline std::string make_name();                          // MEM-38 temporary trap
inline std::vector<int> v;                               // MEM-39 wrong fragment
inline int x = 0;

// performance.md
struct Input {
    int checksum() const { return 0; }
};
inline Input run_case(const Input&) { return {}; }       // PERF harness
inline std::vector<Entry> entries;                       // PERF-11 append loops
inline std::string format(const Entry&) { return {}; }
inline constexpr std::size_t kAvgLineLen = 64;
inline std::string canonical(const std::string&);
inline std::vector<std::string> records_;                // PERF-16 sink examples
struct Host {};
inline constexpr std::array<double, 256> build_gain_table() { return {}; }

// expressions-and-flow.md
enum class Status { Denied, Ok };
inline bool authorize(const Request&) { return true; }
inline std::size_t pending() { return 0; }             // EXPR-10 shadowing example
inline bool streaming = false;
inline std::size_t estimate_size() { return 0; }
inline void ship(std::size_t) {}
inline void report(std::size_t) {}
inline int collect() { return 0; }                     // EXPR-12 narrowing example
struct Size {                                          // EXPR-14 ctor ordering
    int width() const { return 0; }
    int height() const { return 0; }
};
struct SampleRate {};                                  // EXPR-16 spelled type
struct ServiceId {};
struct Service {
    SampleRate rate(ServiceId) const { return {}; }
};
inline Service service;
inline ServiceId id;
struct Frame {                                         // EXPR-23 cast example
    int sequence = 0;
};
inline std::vector<Item> remaining() { return {}; }    // EXPR-27 unsigned wrap
inline void ship(const Item&) {}
struct Order {                                         // EXPR-37 control flow
    bool valid() const { return true; }
    bool is_duplicate() const { return false; }
    int lines() const { return 0; }
};
struct Inventory {
    bool reserve(int) { return true; }
};
inline Inventory inventory;
struct LedgerX {
    void commit(const Order&) {}
};
inline LedgerX ledger;
struct Metrics {
    void count(const char*) {}
};
inline Metrics metrics;
struct Row {};                                         // EXPR-45 range-for trap
struct Connection {
    std::vector<Row> rows() { return {}; }
};
struct Pool {
    Connection acquire() { return {}; }
};
inline Pool connection_pool();
inline void consume(const Row&) {}

// testing-conventions.md
namespace testing {
class Test {
public:
    virtual ~Test() = default;

protected:
    virtual void SetUp() {}
};
}  // namespace testing
#define TEST(suite, name) void suite##_##name()
#define TEST_F(fixture, name) void fixture##_##name()
#define EXPECT_TRUE(x) (void)(x)
#define EXPECT_FALSE(x) (void)(x)
#define EXPECT_EQ(a, b) (void)((a) == (b))
#define EXPECT_CALL(obj, call) (void)(&obj)
#if __cplusplus >= 201703L
using std::nullopt;  // TEST-4 fragment compares against bare nullopt
#endif
struct RingBuffer {                                    // TEST-28 fixture example
    explicit RingBuffer(std::size_t) {}
    void push(int) {}
    std::size_t size() const { return 0; }
};
#if __cplusplus >= 201703L
inline void put(std::string_view, std::string_view, std::chrono::seconds) {}
inline std::string find(std::string_view) { return {}; }
#endif
struct Cache {                                         // TEST-15 right example
#if __cplusplus >= 201703L
    void put(std::string_view, std::string_view, std::chrono::seconds) {}
    std::optional<std::string> find(std::string_view) { return std::nullopt; }
#endif
};
inline Cache* cache_ = nullptr;
inline std::chrono::seconds ttl_{1};
struct FakeClock {
    void advance(std::chrono::seconds) {}
};
inline FakeClock clock_;
inline void handle_user() {}                           // TEST-22 contract checks
using RouteHandler = void (*)();
struct RouteMatch {
    RouteHandler handler() const { return handle_user; }
};
struct Router {
#if __cplusplus >= 201703L
    RouteMatch route(std::string_view) { return {}; }
#endif
};
inline Router router;
enum class ParseErr { kIncomplete, kNotFound };
enum class State { kHeaderDone };
struct ParseReply {
    ParseErr error() const { return ParseErr::kIncomplete; }
};
struct TestParser {
#if __cplusplus >= 201703L
    ParseReply parse(std::string_view) { return {}; }
#endif
    State state_ = State::kHeaderDone;
};
inline TestParser parser;
struct Scanner {
    void scan_token_times(int) {}
};
inline Scanner mock_internal_scanner;
enum class Errc { kNotFound };                         // TEST-32 adapter mapping
struct AdapterReply {
    Errc error() const { return Errc::kNotFound; }
};
struct Adapter {
#if __cplusplus >= 201703L
    AdapterReply open(std::string_view) { return {}; }
#endif
};
inline Adapter adapter;
#if __cplusplus >= 201703L
inline std::optional<int> parse(std::string_view) { return std::nullopt; }  // TEST-4 fragment
#endif

#endif  // TOOLS_STUBS_STUBS_HPP
