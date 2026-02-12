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

---

## SwiftUI Implementation Plan (Adjusted to Current iOS Project)

This plan assumes your Supabase schema changes are already added and focuses on shipping in vertical slices.

### Phase 0 - Align Models and Database Contracts (1-2 sessions)

Goal: make Swift models and Supabase schema match exactly before adding more UI.

- Confirm all id fields use UUID format in both app models and Supabase tables.
- Update iOS models to match schema additions:
  - `venues.venue_type`
  - `venues.museumkaart`
  - `exhibitions` table model
  - `saved_events` table model
- Add small query helpers to `SupabaseService`:
  - fetch museums only
  - fetch exhibitions ending in N days
  - save/unsave event
- Add `UNIQUE` and index checks in SQL docs/migrations (if not already done):
  - `saved_events` unique by saved item
  - index on `exhibitions.end_date`

### Phase 1 - Map and Visit Loop (Core Habit Engine) (2-4 sessions)

Goal: map becomes the daily motivation surface.

- Extend `VenueMapView`:
  - pin style for visited vs unvisited
  - optional filter for museums only
  - quick action to log a visit from map flow
- Extend `VenueDetailView`:
  - "Log visit" CTA
  - mini timeline of recent visits
  - upcoming exhibitions for that venue
- Improve `VisitLogView`:
  - group by month
  - lightweight stats header (total visits, unique venues)

Done criteria:
- You can open app, view map, log visit, and immediately see progress reflected.

### Phase 2 - Discovery Layer (Events + Museums) (2-4 sessions)

Goal: reduce decision fatigue and surface the right options.

- Events tab:
  - add bookmark/save action (to `saved_events`)
  - add "Tonight" / "This week" quick filters
  - improve empty states
- Add museum checklist view:
  - all museumkaart museums
  - visited/unvisited status
  - quick jump to map/detail
- Add "Surprise Me" action:
  - random unvisited museum or relevant event

Done criteria:
- In under 10 seconds, you can decide where to go next.

### Phase 3 - Nudge Layer (Weekly Briefing + Urgency) (2-3 sessions)

Goal: create weekly momentum without manual planning.

- Add "Ending soon" exhibition section in app home/feed.
- Build local weekly digest generation:
  - 3 matching events
  - 1 ending soon exhibition
  - 1 unvisited nearby museum
- Add app-side notification scheduling (local notification MVP first).

Done criteria:
- Weekly reminder appears and drives at least one quick action in app.

### Phase 4 - Progress and Motivation (1-3 sessions)

Goal: make progress visible and rewarding.

- Add personal stats screen:
  - neighborhood coverage
  - venue diversity
  - visit streak
- Add Museumkaart ROI counter:
  - simple annual estimate based on visited museums
- Add shareable personal recap card (optional).

Done criteria:
- You can clearly see your cultural progress over time.

---

## Suggested Backlog in Xcode

Create these work items in order:

1. `Model parity pass` - UUID + new schema fields in Swift models
2. `SupabaseService parity pass` - new query and mutation methods
3. `Map visited state` - visited/unvisited pin rendering
4. `Log visit from venue detail` - one-tap habit loop
5. `Exhibitions model + list` - ending soon query and display
6. `Saved events` - bookmark and list
7. `Museum checklist` - visited progress list
8. `Weekly digest MVP` - local notification + digest screen
9. `Stats + ROI` - progress reinforcement

---

## Practical Build Rules

- Keep every phase as a vertical slice that can run end-to-end.
- Prefer small `SupabaseService` methods with explicit return models.
- Keep table/column naming identical between Swift and Supabase.
- Validate UUID decoding early in each new model to avoid runtime surprises.
- Add one simulator smoke test after each major slice:
  - launch app
  - fetch data
  - perform one write
  - verify UI refreshes
