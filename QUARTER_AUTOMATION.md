# Automatic Quarter Detection System

## Overview

The Drexel scraper now automatically determines the current quarter and year based on the current date, eliminating the need for manual configuration updates every quarter.

## How It Works

The system uses the current date (in Eastern Time Zone) to determine which Drexel quarter is currently active:

### Quarter Mapping

| Quarter | Code | Months | Description |
|---------|------|---------|-------------|
| Fall    | 15   | September - December | Fall semester |
| Winter  | 25   | January - March | Winter quarter |
| Spring  | 35   | March - June | Spring quarter |
| Summer  | 45   | June - September | Summer quarter |

### Implementation Details

- **Timezone**: Uses US/Eastern timezone since Drexel University is located in Philadelphia
- **Automatic Detection**: Runs automatically when the application starts
- **No Manual Updates**: No need to manually change quarter codes or years

## Changes Made

### 1. Modified `src/config.py`

- Added `get_quarter_and_year_for_date()` function for date-based quarter detection
- Added `get_current_quarter_and_year()` function for automatic detection
- Replaced hardcoded `year` and `quarter` variables with automatic detection
- Added logging to show the detected quarter and year

### 2. Created Testing System

- Created `src/test_quarter_detection.py` for comprehensive testing
- Tests all 12 months to ensure correct quarter mapping
- Provides current quarter detection display

## Usage

### Running the Application

The application now automatically detects the current quarter and year when started:

```bash
python3 src/main.py
```

Output will include:
```
Auto-detected current quarter: 45 for year: 2025
```

### Testing the Quarter Detection

To verify the quarter detection logic:

```bash
# Run comprehensive tests
python3 src/test_quarter_detection.py --test

# Show current quarter detection
python3 src/test_quarter_detection.py
```

## Benefits

1. **No Manual Updates**: Never need to update quarter/year configuration again
2. **Automatic Transitions**: System automatically switches to the next quarter when appropriate
3. **Timezone Aware**: Uses Eastern Time Zone for accurate detection
4. **Reliable**: Comprehensive test suite ensures correct quarter mapping
5. **Kubernetes Compatible**: Works seamlessly in containerized environments

## Deployment

### Kubernetes Considerations

The system works automatically in Kubernetes environments:

- No configuration changes needed in Kubernetes manifests
- Uses container's system time in Eastern timezone
- Automatically adjusts for different deployment times

### Environment Variables

No new environment variables are required. The system uses:
- System date/time
- Timezone detection (US/Eastern)

## Monitoring

The application logs the detected quarter and year on startup:
```
Auto-detected current quarter: 45 for year: 2025
```

Monitor these logs to verify correct quarter detection.

## Troubleshooting

### Common Issues

1. **Wrong Quarter Detected**: Verify system time and timezone
2. **Test Failures**: Run `python3 src/test_quarter_detection.py --test` to diagnose

### Manual Override (if needed)

If you need to override the automatic detection for testing:

```python
# In src/config.py, temporarily replace:
year, quarter = get_current_quarter_and_year()

# With:
year, quarter = "2025", "35"  # Example: Spring 2025
```

## Future Enhancements

Potential improvements could include:

1. **Configuration Override**: Environment variable to override automatic detection
2. **Grace Period**: Handle quarter transitions with configurable overlap periods
3. **Academic Calendar API**: Integration with official Drexel academic calendar
4. **Notification System**: Alerts when quarters change

## Technical Details

### Dependencies

- `pytz`: For timezone handling (already in requirements.txt)
- `datetime`: Built-in Python module for date operations

### Functions

- `get_quarter_and_year_for_date(date_obj)`: Determines quarter for specific date
- `get_current_quarter_and_year()`: Gets current quarter and year
- Maintains backward compatibility with existing code

### Testing

The test suite covers:
- All 12 months of the year
- Correct quarter code mapping
- Year handling
- Edge cases and transitions

This automated system ensures the Drexel scraper always uses the correct quarter without manual intervention.