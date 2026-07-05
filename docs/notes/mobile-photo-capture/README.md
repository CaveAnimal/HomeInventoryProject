# Mobile Photo Capture

## Idea

Use an old iPhone as a capture device for the inventory app without installing new apps.

## Desired Workflow

```text
Open Home Inventory in Safari
Choose or create a container
Tap Take Photo
Camera opens
Take picture
Tap Use Photo
Upload immediately
Repeat for more angles
Review detected items
```

## Browser Capability

Safari can use a standard file input to open the camera:

```html
<input type="file" accept="image/*" capture="environment">
```

This should not require installing anything on the iPhone.

## Important Limitation

Fully automatic background transfer from the native iPhone Camera app is probably not reliable without installing something or using iCloud Photos sync. The realistic no-install workflow is camera capture from inside the web app.

## Implementation Notes

- Add a mobile-friendly capture page.
- Keep buttons large and text short.
- Support multiple photos per container.
- Support "take another" immediately after upload.
- Let the user assign photos to an existing container or create a new one.
- Later, consider watched-folder import for iCloud/Photos sync.

