# MinuteMate Frontend

A modern, responsive web interface for the MinuteMate AI-powered meeting minutes generator.

## 🌟 Features

### User Interface
- **Drag & Drop File Upload**: Intuitive file upload with drag-and-drop support
- **Real-time Progress Tracking**: Live updates during processing with visual progress indicators
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Professional Styling**: Clean, modern interface with smooth animations

### File Handling
- **Multi-format Support**: Audio (MP3, WAV, FLAC, M4A, AAC, OGG) and Video (MP4, AVI, MOV, MKV, WMV)
- **Client-side Validation**: Immediate feedback on file type and size validation
- **Security Checks**: File type verification and size limit enforcement
- **Progress Visualization**: Step-by-step processing status with icons and descriptions

### User Experience
- **Toast Notifications**: Non-intrusive success, error, and warning messages
- **Loading States**: Clear loading indicators during API calls
- **Error Handling**: User-friendly error messages with retry options
- **System Health**: Real-time system status monitoring

## 📁 File Structure

```
frontend/
├── index.html          # Main application interface
├── demo.html           # Feature demonstration page
├── styles.css          # Complete CSS styling
├── script.js           # JavaScript functionality
└── README.md           # This file
```

## 🚀 Getting Started

### Prerequisites
- MinuteMate backend server running on `http://localhost:5000`
- Modern web browser with JavaScript enabled

### Running the Frontend

1. **Via Flask Backend** (Recommended):
   ```bash
   # Start the backend server
   cd backend
   python run.py
   
   # Access frontend at:
   # http://localhost:5000/frontend/
   ```

2. **Direct File Access**:
   ```bash
   # Open directly in browser
   open frontend/index.html
   ```

3. **Local Web Server**:
   ```bash
   # Using Python's built-in server
   cd frontend
   python -m http.server 8080
   
   # Access at http://localhost:8080
   ```

## 🎯 Usage Guide

### Basic Workflow

1. **Upload File**:
   - Drag and drop an audio/video file onto the upload area
   - Or click to browse and select a file
   - File is validated for type and size

2. **Configure Options**:
   - Select language (auto-detect or specific language)
   - Choose output format (Robert's Rules, Informal, Corporate)

3. **Start Processing**:
   - Click "Start Processing" to upload and begin transcription
   - Monitor real-time progress through processing stages

4. **Download Results**:
   - Download DOCX file when processing completes
   - View processing summary and statistics

### Processing Stages

1. **Upload & Validation**: File upload and security validation
2. **Transcription**: Audio-to-text conversion using AI
3. **Content Analysis**: Identification of motions, votes, and discussions
4. **Formatting**: Professional meeting minutes generation

## 🎨 Design System

### Color Palette
- **Primary**: `#2563eb` (Blue)
- **Secondary**: `#10b981` (Green)
- **Danger**: `#ef4444` (Red)
- **Warning**: `#f59e0b` (Amber)
- **Gray Scale**: `#f9fafb` to `#111827`

### Typography
- **Font Family**: System fonts (-apple-system, BlinkMacSystemFont, Segoe UI)
- **Headings**: 600-700 weight
- **Body**: 400 weight, 1.6 line height

### Components
- **Buttons**: Rounded corners, hover effects, disabled states
- **Cards**: Subtle shadows, rounded borders
- **Progress Bars**: Gradient fills, smooth animations
- **Toasts**: Slide-in animations, auto-dismiss

## 🔧 Technical Details

### JavaScript Architecture
- **Class-based Structure**: `MinuteMateApp` class manages all functionality
- **Event-driven**: Comprehensive event handling for user interactions
- **API Integration**: RESTful API communication with error handling
- **State Management**: Simple state management for upload/processing flow

### CSS Features
- **CSS Custom Properties**: Consistent theming with CSS variables
- **Flexbox & Grid**: Modern layout techniques
- **Responsive Design**: Mobile-first approach with breakpoints
- **Animations**: Smooth transitions and loading states

### Browser Support
- **Modern Browsers**: Chrome 80+, Firefox 75+, Safari 13+, Edge 80+
- **Features Used**: Fetch API, CSS Grid, CSS Custom Properties
- **Fallbacks**: Graceful degradation for older browsers

## 📱 Responsive Breakpoints

- **Desktop**: 1200px+ (Full layout)
- **Tablet**: 768px-1199px (Adapted layout)
- **Mobile**: <768px (Stacked layout)

## 🔒 Security Features

### Client-side Validation
- File type checking (MIME type and extension)
- File size validation (500MB limit)
- Input sanitization for form data

### Error Handling
- Comprehensive error catching and user feedback
- Network error handling with retry options
- Graceful degradation for API failures

## 🎛️ Configuration

### API Endpoint
Update the API base URL in `script.js`:
```javascript
this.apiBaseUrl = 'http://localhost:5000';
```

### File Limits
Modify validation limits in the `selectFile` method:
```javascript
const maxSize = 500 * 1024 * 1024; // 500MB
```

### Supported File Types
Update allowed types in the `selectFile` method:
```javascript
const allowedTypes = [
    'audio/mpeg', 'audio/wav', 'audio/flac',
    'video/mp4', 'video/avi', 'video/quicktime'
];
```

## 🚀 Deployment

### Production Considerations
1. **HTTPS**: Ensure secure connections in production
2. **CDN**: Consider using CDN for static assets
3. **Compression**: Enable gzip compression for better performance
4. **Caching**: Implement appropriate cache headers

### Environment Variables
- `API_BASE_URL`: Backend API endpoint
- `MAX_FILE_SIZE`: Maximum upload file size
- `SUPPORTED_FORMATS`: Comma-separated list of supported formats

## 🐛 Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Ensure backend CORS is properly configured
   - Check API endpoint URL

2. **File Upload Fails**:
   - Verify file size is under 500MB
   - Check file format is supported
   - Ensure backend server is running

3. **Progress Not Updating**:
   - Check network connection
   - Verify job ID is valid
   - Check browser console for errors

### Debug Mode
Enable debug logging by adding to browser console:
```javascript
localStorage.setItem('debug', 'true');
```

## 🤝 Contributing

1. Follow existing code style and structure
2. Test on multiple browsers and devices
3. Ensure responsive design works correctly
4. Add appropriate error handling
5. Update documentation for new features

## 📄 License

This frontend is part of the MinuteMate project. See the main project README for license information.
