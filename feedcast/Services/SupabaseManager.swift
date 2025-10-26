//
//  SupabaseManager.swift
//  feedcast
//
//  Singleton manager for Supabase client
//

import Foundation
import Supabase

class SupabaseManager {
    
    // MARK: - Singleton
    static let shared = SupabaseManager()
    
    // MARK: - Properties
    let client: SupabaseClient
    
    // MARK: - Initialization
    private init() {
        guard Config.isSupabaseConfigured else {
            fatalError("""
                ⚠️ Supabase not configured!
                
                Please update Config.swift with your Supabase credentials:
                1. Go to https://supabase.com
                2. Open your project
                3. Go to Settings → API
                4. Copy Project URL and anon key
                5. Update Config.swift
                """)
        }
        
        client = SupabaseClient(
            supabaseURL: URL(string: Config.supabaseURL)!,
            supabaseKey: Config.supabaseAnonKey
        )
        
        print("✅ Supabase client initialized")
    }
    
    // MARK: - Helper Methods
    
    /// Get current user ID from auth session
    func getCurrentUserId() async throws -> UUID? {
        let session = try await client.auth.session
        return session.user.id
    }
    
    /// Check if user is authenticated
    func isAuthenticated() async -> Bool {
        do {
            _ = try await client.auth.session
            return true
        } catch {
            return false
        }
    }
}

