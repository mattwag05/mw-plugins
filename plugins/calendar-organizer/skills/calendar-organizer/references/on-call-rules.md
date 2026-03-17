# On-Call Rules

Rules for handling on-call schedule entries.

## Detection

An event is on-call when the text contains:
- "on call" or "on-call" or "oncall"
- "call" as a standalone scheduling designation
- "OC" abbreviation in scheduling context

## Creating On-Call Events

When "on call" is detected:
1. Create the regular daytime event (if any) as normal
2. Create a separate "On Call" event using the rules below

## On-Call Time Rules by Day

| Day | On-Call Start | On-Call End | Notes |
|-----|---------------|-------------|-------|
| Monday | 5:00 PM | 7:30 AM (Tuesday) | After regular afternoon duty |
| Tuesday | 8:00 PM | 7:30 AM (Wednesday) | Later start (after evening duties) |
| Wednesday | 5:00 PM | 7:30 AM (Thursday) | After regular afternoon duty |
| Thursday | 8:00 PM | 7:30 AM (Friday) | Later start (after evening duties) |
| Friday | 5:00 PM | 7:30 AM (Saturday) | After regular afternoon duty |
| Saturday | 8:00 AM | 7:30 AM (Sunday) | Full 24-hour coverage |
| Sunday | 8:00 AM | 7:30 AM (Monday) | Full 24-hour coverage |

## Adjustments

- If the person has afternoon duty ending at a different time, adjust on-call start accordingly
- If on-call explicitly states a start time, use that instead of defaults
- Weekend on-call is typically 24-hour coverage starting in the morning

## ICS Considerations

On-call events span midnight, so they require:
- Start date: the on-call day
- End date: the following day
- The ICS generator handles overnight events automatically

## Example

Schedule entry: "Clinic AM / On Call" on Wednesday March 15

Creates two events:
1. **Clinic**: Wed Mar 15, 8:00 AM - 12:00 PM
2. **On Call**: Wed Mar 15, 5:00 PM - Thu Mar 16, 7:30 AM
