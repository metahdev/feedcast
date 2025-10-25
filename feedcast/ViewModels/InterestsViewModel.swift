//
//  InterestsViewModel.swift
//  feedcast
//
//  ViewModel for managing user interests and preferences.
//

import Foundation
import Combine

@MainActor
class InterestsViewModel: ObservableObject {
    
    // MARK: - Published Properties
    @Published var interests: [Interest] = []
    @Published var newInterestName = ""
    @Published var selectedCategory: InterestCategory = .technology
    @Published var isLoading = false
    @Published var error: Error?
    @Published var searchText = ""
    
    // MARK: - Private Properties
    private let userService = UserService.shared
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - Computed Properties
    
    var filteredInterests: [Interest] {
        if searchText.isEmpty {
            return interests
        }
        return interests.filter {
            $0.name.localizedCaseInsensitiveContains(searchText) ||
            $0.category.rawValue.localizedCaseInsensitiveContains(searchText)
        }
    }
    
    var activeInterests: [Interest] {
        filteredInterests.filter { $0.isActive }
    }
    
    var inactiveInterests: [Interest] {
        filteredInterests.filter { !$0.isActive }
    }
    
    var groupedInterests: [InterestCategory: [Interest]] {
        Dictionary(grouping: filteredInterests) { $0.category }
    }
    
    // MARK: - Initialization
    
    init() {
        loadInterests()
    }
    
    // MARK: - Public Methods
    
    func loadInterests() {
        interests = userService.getInterests()
    }
    
    func addInterest() {
        let trimmed = newInterestName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        
        let interest = Interest(
            name: trimmed,
            category: selectedCategory,
            isActive: true
        )
        
        Task {
            isLoading = true
            defer { isLoading = false }
            
            do {
                try await userService.addInterest(interest)
                loadInterests()
                newInterestName = ""
            } catch {
                self.error = error
            }
        }
    }
    
    func removeInterest(_ interest: Interest) {
        Task {
            isLoading = true
            defer { isLoading = false }
            
            do {
                try await userService.removeInterest(id: interest.id)
                loadInterests()
            } catch {
                self.error = error
            }
        }
    }
    
    func toggleInterest(_ interest: Interest) {
        Task {
            isLoading = true
            defer { isLoading = false }
            
            do {
                try await userService.toggleInterest(id: interest.id)
                loadInterests()
            } catch {
                self.error = error
            }
        }
    }
    
    func canAddInterest() -> Bool {
        let trimmed = newInterestName.trimmingCharacters(in: .whitespacesAndNewlines)
        return !trimmed.isEmpty && !interests.contains { $0.name.lowercased() == trimmed.lowercased() }
    }
}

