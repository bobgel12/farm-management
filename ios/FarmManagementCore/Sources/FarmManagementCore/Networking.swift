import Foundation

public enum APIError: LocalizedError, Equatable {
    case invalidURL
    case transport(String)
    case unauthorized
    case server(statusCode: Int, message: String)
    case decoding(String)
    case unknown

    public var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL."
        case .transport(let message):
            return "Network error: \(message)"
        case .unauthorized:
            return "Your session is invalid. Please log in again."
        case .server(_, let message):
            return message
        case .decoding(let message):
            return "Failed to parse server response: \(message)"
        case .unknown:
            return "An unknown error occurred."
        }
    }
}

public struct APIMessageError: Decodable {
    public let message: String?
    public let error: String?
    public let detail: String?
}

public struct PaginatedResponse<T: Decodable>: Decodable {
    public let count: Int
    public let next: String?
    public let previous: String?
    public let results: [T]
}

public enum FlexibleListResponse<T: Decodable>: Decodable {
    case paginated(PaginatedResponse<T>)
    case array([T])

    public var values: [T] {
        switch self {
        case .paginated(let paginated):
            return paginated.results
        case .array(let array):
            return array
        }
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let paginated = try? container.decode(PaginatedResponse<T>.self) {
            self = .paginated(paginated)
            return
        }
        self = .array(try container.decode([T].self))
    }
}

public protocol TokenProvider {
    func readToken() -> String?
}

public struct APIClient {
    public let baseURL: URL
    public let session: URLSession
    public let tokenProvider: TokenProvider?
    public var decoder: JSONDecoder

    public init(
        baseURL: URL,
        session: URLSession = .shared,
        tokenProvider: TokenProvider? = nil
    ) {
        self.baseURL = baseURL
        self.session = session
        self.tokenProvider = tokenProvider
        self.decoder = JSONDecoder()
    }

    public func request<T: Decodable>(
        path: String,
        method: String = "GET",
        body: Data? = nil,
        authenticated: Bool = true
    ) async throws -> T {
        guard let url = URL(string: path, relativeTo: baseURL) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.httpBody = body
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if authenticated, let token = tokenProvider?.readToken(), token.isEmpty == false {
            request.setValue("Token \(token)", forHTTPHeaderField: "Authorization")
        }

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw APIError.transport(error.localizedDescription)
        }

        guard let http = response as? HTTPURLResponse else {
            throw APIError.unknown
        }

        if http.statusCode == 401 {
            throw APIError.unauthorized
        }

        guard (200..<300).contains(http.statusCode) else {
            let message: String
            if let apiError = try? decoder.decode(APIMessageError.self, from: data) {
                message = apiError.error ?? apiError.message ?? apiError.detail ?? "Server error (\(http.statusCode))"
            } else if let text = String(data: data, encoding: .utf8), text.isEmpty == false {
                message = "Server error (\(http.statusCode)): \(text)"
            } else {
                message = "Server error (\(http.statusCode))"
            }
            throw APIError.server(statusCode: http.statusCode, message: message)
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decoding(error.localizedDescription)
        }
    }
}
