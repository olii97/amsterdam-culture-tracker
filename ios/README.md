# Amsterdam Culture Tracker - iOS App

Native SwiftUI app for browsing Amsterdam cultural events, viewing venues on a map, and tracking your visits.

## Requirements

- **Xcode 15+** (for iOS 17+ target)
- **macOS Sonoma or later**
- Active Supabase project (same one used by the Python pipeline)

## Setup

### 1. Install Dependencies

The project uses Swift Package Manager. Xcode will automatically fetch dependencies when you open the project, but if needed:

1. Open `AmsterdamCultureTracker.xcodeproj` in Xcode
2. File → Add Package Dependencies
3. Add `https://github.com/supabase/supabase-swift` (v2.0.0+)

### 2. Configure Supabase Credentials

Open `AmsterdamCultureTracker/App/Config.swift` and replace the placeholder values:

```swift
static let supabaseURL = "https://xxxxx.supabase.co"
static let supabaseAnonKey = "your-anon-key-here"
```

Find these values in your Supabase dashboard:
- Go to https://supabase.com/dashboard/project/_/settings/api
- Copy **Project URL** → `supabaseURL`
- Copy **anon/public key** → `supabaseAnonKey`

### 3. Add Files to Xcode Project

After creating all the Swift files, you need to add them to your Xcode project:

1. In Xcode, right-click on the `AmsterdamCultureTracker` group (yellow folder icon)
2. Select "Add Files to AmsterdamCultureTracker..."
3. Navigate to `ios/AmsterdamCultureTracker/AmsterdamCultureTracker/`
4. Select the `App`, `Models`, `Services`, and `Views` folders
5. Make sure "Create groups" is selected and "AmsterdamCultureTracker" target is checked
6. Click "Add"

### 4. Build and Run

1. Select a simulator (iPhone 15 or later recommended)
2. Press ⌘R or click the Play button
3. The app will build and launch in the simulator

## Features

### Events Tab
- Browse upcoming events from all venues
- Filter by event type (concert, cabaret, debate, etc.)
- Filter by venue
- Tap an event to see full details and ticket link
- Pull to refresh

### Map Tab
- See all 4 Amsterdam venues as pins on a map
- Tap a pin to view venue details
- Centered on Amsterdam (52.37°N, 4.90°E)

### Visits Tab
- Log venue visits with date and notes
- Browse your visit history
- Tap a visit to see venue details

## Project Structure

```
AmsterdamCultureTracker/
├── App/
│   ├── AmsterdamCultureTrackerApp.swift  # Entry point with TabView
│   └── Config.swift                       # Supabase credentials
├── Models/
│   ├── Event.swift                        # Matches 'events' table
│   ├── Venue.swift                        # Matches 'venues' table
│   ├── VenueVisit.swift                   # Matches 'venue_visits' table
│   └── EventType.swift                    # Event type enum with icons
├── Services/
│   └── SupabaseService.swift             # All database queries
└── Views/
    ├── Events/
    │   ├── EventsListView.swift          # Main events list
    │   ├── EventRow.swift                # Single event row
    │   └── EventDetailView.swift         # Event detail screen
    ├── Venues/
    │   ├── VenueMapView.swift            # Map with venue pins
    │   └── VenueDetailView.swift         # Venue detail screen
    ├── Visits/
    │   ├── VisitLogView.swift            # All visits list
    │   └── AddVisitSheet.swift           # Log visit modal
    └── Components/
        └── EventTypeFilterChips.swift    # Filter chip component
```

## Troubleshooting

### "Invalid Supabase URL" error
- Check that you've replaced the placeholder values in `Config.swift`
- Make sure the URL starts with `https://` and ends with `.supabase.co`

### Build errors about missing files
- Make sure you've added all Swift files to the Xcode project (see Setup step 3)
- In Xcode, check Build Phases → Compile Sources to see which files are included

### No events/venues showing
- Verify your Supabase credentials are correct
- Check that the Python pipeline has run and populated the database
- In Supabase dashboard, verify you have data in the `events` and `venues` tables

### Map not showing
- Make sure you're targeting iOS 17+ (uses new MapKit API)
- Check that venues have valid latitude/longitude values in Supabase

## Next Steps

Per the project roadmap (Phase 4), future enhancements include:
- Push notifications for new events
- Event suggestions based on your visit history
- Search functionality
- Event calendar view
- Share events with friends
