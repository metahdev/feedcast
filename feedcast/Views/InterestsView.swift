//
//  InterestsView.swift
//  feedcast
//
//  View for managing user interests that personalize podcast generation.
//

import SwiftUI

struct InterestsView: View {
    @StateObject private var viewModel = InterestsViewModel()
    @Environment(\.dismiss) private var dismiss
    @State private var showingAddInterest = false
    
    var body: some View {
        NavigationStack {
            List {
                // Summary Section
                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Your Interests")
                            .font(.title3)
                            .fontWeight(.bold)
                        
                        Text("Manage topics that personalize your AI-generated podcasts")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        
                        HStack(spacing: 16) {
                            StatCard(
                                title: "Active",
                                value: "\(viewModel.activeInterests.count)",
                                color: .green
                            )
                            
                            StatCard(
                                title: "Total",
                                value: "\(viewModel.interests.count)",
                                color: .blue
                            )
                        }
                        .padding(.top, 8)
                    }
                    .padding(.vertical, 8)
                }
                .listRowBackground(Color.clear)
                
                // Active Interests
                if !viewModel.activeInterests.isEmpty {
                    Section {
                        ForEach(viewModel.activeInterests) { interest in
                            InterestRow(
                                interest: interest,
                                onToggle: { viewModel.toggleInterest(interest) },
                                onDelete: { viewModel.removeInterest(interest) }
                            )
                        }
                    } header: {
                        Text("Active Interests")
                    }
                }
                
                // Inactive Interests
                if !viewModel.inactiveInterests.isEmpty {
                    Section {
                        ForEach(viewModel.inactiveInterests) { interest in
                            InterestRow(
                                interest: interest,
                                onToggle: { viewModel.toggleInterest(interest) },
                                onDelete: { viewModel.removeInterest(interest) }
                            )
                        }
                    } header: {
                        Text("Inactive Interests")
                    }
                }
                
                // Browse by Category
                Section {
                    ForEach(InterestCategory.allCases, id: \.self) { category in
                        NavigationLink(destination: CategoryDetailView(category: category)) {
                            HStack {
                                Text(category.emoji)
                                    .font(.title3)
                                Text(category.rawValue)
                                Spacer()
                                let count = viewModel.interests.filter { $0.category == category }.count
                                if count > 0 {
                                    Text("\(count)")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                    }
                } header: {
                    Text("Browse by Category")
                }
            }
            .navigationTitle("Interests")
            .navigationBarTitleDisplayMode(.inline)
            .searchable(text: $viewModel.searchText, prompt: "Search interests")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Done") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showingAddInterest = true
                    } label: {
                        Image(systemName: "plus.circle.fill")
                    }
                }
            }
            .sheet(isPresented: $showingAddInterest) {
                AddInterestView(viewModel: viewModel)
            }
        }
    }
}

// MARK: - Stat Card

struct StatCard: View {
    let title: String
    let value: String
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
            
            Text(value)
                .font(.title2)
                .fontWeight(.bold)
                .foregroundStyle(color)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(color.opacity(0.1))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

// MARK: - Interest Row

struct InterestRow: View {
    let interest: Interest
    let onToggle: () -> Void
    let onDelete: () -> Void
    
    var body: some View {
        HStack(spacing: 12) {
            Text(interest.category.emoji)
                .font(.title3)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(interest.name)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(interest.category.rawValue)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            
            Spacer()
            
            Toggle("", isOn: Binding(
                get: { interest.isActive },
                set: { _ in onToggle() }
            ))
            .labelsHidden()
        }
        .swipeActions(edge: .trailing, allowsFullSwipe: true) {
            Button(role: .destructive) {
                onDelete()
            } label: {
                Label("Delete", systemImage: "trash")
            }
        }
    }
}

// MARK: - Category Detail View

struct CategoryDetailView: View {
    let category: InterestCategory
    @StateObject private var viewModel = InterestsViewModel()
    
    var categoryInterests: [Interest] {
        viewModel.interests.filter { $0.category == category }
    }
    
    var body: some View {
        List {
            Section {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text(category.emoji)
                            .font(.largeTitle)
                        
                        VStack(alignment: .leading, spacing: 4) {
                            Text(category.rawValue)
                                .font(.title2)
                                .fontWeight(.bold)
                            
                            Text("\(categoryInterests.count) interests")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                .padding(.vertical, 8)
            }
            .listRowBackground(Color.clear)
            
            if categoryInterests.isEmpty {
                Section {
                    Text("No interests in this category yet")
                        .foregroundStyle(.secondary)
                }
            } else {
                Section {
                    ForEach(categoryInterests) { interest in
                        InterestRow(
                            interest: interest,
                            onToggle: { viewModel.toggleInterest(interest) },
                            onDelete: { viewModel.removeInterest(interest) }
                        )
                    }
                }
            }
        }
        .navigationTitle(category.rawValue)
        .navigationBarTitleDisplayMode(.inline)
    }
}

// MARK: - Add Interest View

struct AddInterestView: View {
    @ObservedObject var viewModel: InterestsViewModel
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Interest name", text: $viewModel.newInterestName)
                        .textInputAutocapitalization(.words)
                } header: {
                    Text("Name")
                } footer: {
                    Text("Enter a topic you'd like to hear about in your podcasts")
                }
                
                Section("Category") {
                    Picker("Category", selection: $viewModel.selectedCategory) {
                        ForEach(InterestCategory.allCases, id: \.self) { category in
                            HStack {
                                Text(category.emoji)
                                Text(category.rawValue)
                            }
                            .tag(category)
                        }
                    }
                    .pickerStyle(.wheel)
                }
            }
            .navigationTitle("Add Interest")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .confirmationAction) {
                    Button("Add") {
                        viewModel.addInterest()
                        dismiss()
                    }
                    .disabled(!viewModel.canAddInterest())
                }
            }
        }
    }
}

#Preview {
    InterestsView()
}

