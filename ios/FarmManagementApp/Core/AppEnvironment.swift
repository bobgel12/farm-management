import Foundation

enum AppEnvironment {
    static var apiBaseURL: URL {
        #if DEBUG
        let key = "API_BASE_URL_DEBUG"
        #else
        let key = "API_BASE_URL_RELEASE"
        #endif

        if let configured = Bundle.main.object(forInfoDictionaryKey: key) as? String,
           let url = URL(string: configured), configured.isEmpty == false {
            return url
        }
        return URL(string: "https://farm-management-production-54e4.up.railway.app/api/")!
    }

    static let deploymentTarget = "iOS 16.0+"
    static let devicePolicy = "iPhone-first"
}
