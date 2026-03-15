import EventKit
import Foundation

/// Fetches incomplete reminders and outputs JSON
@main
struct RemindersCLI {
    static func main() async {
        let eventStore = EKEventStore()

        // Request access
        do {
            let granted = try await eventStore.requestFullAccessToReminders()
            guard granted else {
                printError("Reminders access denied. Grant access in System Settings.")
                exit(1)
            }
        } catch {
            printError("Failed to request access: \(error.localizedDescription)")
            exit(1)
        }

        // Get all reminder calendars
        let calendars = eventStore.calendars(for: .reminder)

        // Fetch incomplete reminders
        let predicate = eventStore.predicateForIncompleteReminders(
            withDueDateStarting: nil,
            ending: nil,
            calendars: calendars
        )

        let reminders = await withCheckedContinuation { continuation in
            eventStore.fetchReminders(matching: predicate) { reminders in
                continuation.resume(returning: reminders)
            }
        }

        guard let reminders = reminders else {
            printJSON([])
            return
        }

        // Convert to JSON
        let output: [[String: Any]] = reminders.compactMap { reminder in
            var item: [String: Any] = [
                "title": reminder.title ?? "Untitled",
                "list": reminder.calendar.title,
                "priority": reminder.priority,
                "completed": reminder.isCompleted
            ]

            if let dueDate = reminder.dueDateComponents?.date {
                let formatter = ISO8601DateFormatter()
                item["dueDate"] = formatter.string(from: dueDate)
            }

            if let notes = reminder.notes, !notes.isEmpty {
                item["notes"] = notes
            }

            return item
        }

        printJSON(output)
    }

    static func printJSON(_ items: [[String: Any]]) {
        if let data = try? JSONSerialization.data(withJSONObject: items, options: [.prettyPrinted, .sortedKeys]),
           let string = String(data: data, encoding: .utf8) {
            print(string)
        } else {
            print("[]")
        }
    }

    static func printError(_ message: String) {
        let error = ["error": message]
        if let data = try? JSONSerialization.data(withJSONObject: error),
           let string = String(data: data, encoding: .utf8) {
            fputs(string + "\n", stderr)
        }
    }
}
