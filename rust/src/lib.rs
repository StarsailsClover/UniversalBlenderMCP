use pyo3::prelude::*;
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

/// Capture Blender viewport using native OS APIs
#[pyfunction]
fn capture_viewport(output_path: Option<String>, width: u32, height: u32) -> PyResult<String> {
    let path = match output_path {
        Some(p) => p,
        None => {
            let timestamp = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs();
            format!("/tmp/ubm_capture_{}.png", timestamp)
        }
    };
    
    #[cfg(target_os = "windows")]
    {
        return capture_windows(&path, width, height);
    }
    
    #[cfg(target_os = "macos")]
    {
        return capture_macos(&path, width, height);
    }
    
    #[cfg(target_os = "linux")]
    {
        return capture_linux(&path, width, height);
    }
    
    #[cfg(not(any(target_os = "windows", target_os = "macos", target_os = "linux")))]
    {
        Err(PyErr::new::<pyo3::exceptions::PyNotImplementedError, _>(
            "Screenshot not implemented for this platform"
        ))
    }
}

/// Windows implementation
#[cfg(target_os = "windows")]
fn capture_windows(path: &str, width: u32, height: u32) -> PyResult<String> {
    use windows::Win32::Foundation::{HWND, RECT};
    use windows::Win32::Graphics::Gdi::{GetDC, ReleaseDC, BitBlt, SRCCOPY, CreateCompatibleDC, CreateCompatibleBitmap, SelectObject, DeleteObject, DeleteDC, GetDIBits, BITMAPINFOHEADER, BI_RGB};
    use windows::Win32::UI::WindowsAndMessaging::{FindWindowW, GetWindowRect, GetClientRect};
    use std::ffi::OsStr;
    use std::os::windows::ffi::OsStrExt;
    
    unsafe {
        // Find Blender window
        let class_name: Vec<u16> = OsStr::new("GHOST_WindowClass")
            .encode_wide()
            .chain(Some(0))
            .collect();
        let hwnd = FindWindowW(
            windows::core::PCWSTR(class_name.as_ptr()),
            windows::core::PCWSTR::null()
        );
        
        if hwnd.0 == 0 {
            return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Blender window not found"
            ));
        }
        
        // Get window dimensions
        let mut client_rect = RECT::default();
        GetClientRect(hwnd, &mut client_rect)?;
        
        let w = (client_rect.right - client_rect.left) as u32;
        let h = (client_rect.bottom - client_rect.top) as u32;
        
        // Get device context
        let hdc_window = GetDC(hwnd);
        let hdc_mem = CreateCompatibleDC(hdc_window);
        let hbitmap = CreateCompatibleBitmap(hdc_window, w as i32, h as i32);
        SelectObject(hdc_mem, hbitmap);
        
        // Copy screen to bitmap
        BitBlt(
            hdc_mem,
            0, 0,
            w as i32, h as i32,
            hdc_window,
            0, 0,
            SRCCOPY
        )?;
        
        // Get bitmap data
        let mut bmi = BITMAPINFOHEADER {
            biSize: std::mem::size_of::<BITMAPINFOHEADER>() as u32,
            biWidth: w as i32,
            biHeight: h as i32,
            biPlanes: 1,
            biBitCount: 24,
            biCompression: BI_RGB.0 as u32,
            biSizeImage: 0,
            biXPelsPerMeter: 0,
            biYPelsPerMeter: 0,
            biClrUsed: 0,
            biClrImportant: 0,
        };
        
        let mut buffer: Vec<u8> = vec![0; (w * h * 3) as usize];
        GetDIBits(
            hdc_mem,
            hbitmap,
            0,
            h,
            Some(buffer.as_mut_ptr() as *mut _),  
            &mut bmi as *mut _ as *mut _,
            0
        );
        
        // Cleanup
        DeleteObject(hbitmap)?;
        DeleteDC(hdc_mem)?;
        ReleaseDC(hwnd, hdc_window)?;
        
        // Convert BGR to RGB and save as PNG
        let mut rgb_buffer: Vec<u8> = vec![0; (w * h * 3) as usize];
        for i in 0..(w * h) as usize {
            let idx = i * 3;
            rgb_buffer[idx] = buffer[idx + 2];     // R
            rgb_buffer[idx + 1] = buffer[idx + 1]; // G
            rgb_buffer[idx + 2] = buffer[idx];     // B
        }
        
        // Save using image crate
        let img = image::RgbImage::from_raw(w, h, rgb_buffer)
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Failed to create image"
            ))?;
        
        img.save(path)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                format!("Failed to save image: {}", e)
            ))?;
        
        Ok(path.to_string())
    }
}

/// macOS implementation
#[cfg(target_os = "macos")]
fn capture_macos(path: &str, width: u32, height: u32) -> PyResult<String> {
    // For now, return error - full implementation would use Core Graphics
    // This is a placeholder for the actual macOS implementation
    Err(PyErr::new::<pyo3::exceptions::PyNotImplementedError, _>(
        "macOS screenshot implementation requires Core Graphics framework"
    ))
}

/// Linux implementation
#[cfg(target_os = "linux")]
fn capture_linux(path: &str, width: u32, height: u32) -> PyResult<String> {
    // For now, return error - full implementation would use X11
    // This is a placeholder for the actual Linux implementation
    Err(PyErr::new::<pyo3::exceptions::PyNotImplementedError, _>(
        "Linux screenshot implementation requires X11"
    ))
}

/// Check if Blender is running
#[pyfunction]
fn is_blender_running() -> PyResult<bool> {
    #[cfg(target_os = "windows")]
    {
        use windows::Win32::UI::WindowsAndMessaging::{FindWindowW, GetWindowTextW};
        use std::ffi::OsStr;
        use std::os::windows::ffi::OsStrExt;
        
        unsafe {
            let class_name: Vec<u16> = OsStr::new("GHOST_WindowClass")
                .encode_wide()
                .chain(Some(0))
                .collect();
            let hwnd = FindWindowW(
                windows::core::PCWSTR(class_name.as_ptr()),
                windows::core::PCWSTR::null()
            );
            
            Ok(hwnd.0 != 0)
        }
    }
    
    #[cfg(not(target_os = "windows"))]
    {
        // For other platforms, check process
        use std::process::Command;
        
        let output = Command::new("pgrep")
            .arg("-x")
            .arg("blender")
            .output();
        
        match output {
            Ok(o) => Ok(o.status.success() && !o.stdout.is_empty()),
            Err(_) => Ok(false)
        }
    }
}

/// List all visible Blender windows
#[pyfunction]
fn list_blender_windows() -> PyResult<Vec<(u64, String)>> {
    let mut windows = Vec::new();
    
    #[cfg(target_os = "windows")]
    {
        use windows::Win32::UI::WindowsAndMessaging::{EnumWindows, GetWindowTextW, IsWindowVisible};
        use windows::Win32::Foundation::{BOOL, HWND, LPARAM};
        use std::ffi::OsString;
        use std::os::windows::ffi::OsStringExt;
        
        unsafe {
            let windows_ptr: *mut Vec<(u64, String)> = &mut windows;
            
            extern "system" fn enum_callback(hwnd: HWND, lparam: LPARAM) -> BOOL {
                unsafe {
                    let windows = &mut *(lparam.0 as *mut Vec<(u64, String)>);
                    
                    if IsWindowVisible(hwnd).as_bool() {
                        let mut text: [u16; 256] = [0; 256];
                        let len = GetWindowTextW(hwnd, &mut text);
                        
                        if len > 0 {
                            let title = OsString::from_wide(&text[..len as usize])
                                .to_string_lossy()
                                .to_string();
                            
                            if title.contains("Blender") {
                                windows.push((hwnd.0 as u64, title));
                            }
                        }
                    }
                    
                    BOOL(1) // Continue enumeration
                }
            }
            
            EnumWindows(
                Some(enum_callback),
                LPARAM(windows_ptr as isize)
            );
        }
    }
    
    Ok(windows)
}

/// Get window position and size
#[pyfunction]
fn get_window_rect(window_id: u64) -> PyResult<(i32, i32, i32, i32)> {
    #[cfg(target_os = "windows")]
    {
        use windows::Win32::Foundation::{HWND, RECT};
        use windows::Win32::UI::WindowsAndMessaging::GetWindowRect;
        
        unsafe {
            let hwnd = HWND(window_id as *mut _);
            let mut rect = RECT::default();
            
            GetWindowRect(hwnd, &mut rect)?;
            
            Ok((
                rect.left,
                rect.top,
                rect.right - rect.left,  // width
                rect.bottom - rect.top   // height
            ))
        }
    }
    
    #[cfg(not(target_os = "windows"))]
    {
        Err(PyErr::new::<pyo3::exceptions::PyNotImplementedError, _>(
            "Window rect only implemented for Windows"
        ))
    }
}

#[pymodule]
fn ubm_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(capture_viewport, m)?)?;
    m.add_function(wrap_pyfunction!(is_blender_running, m)?)?;
    m.add_function(wrap_pyfunction!(list_blender_windows, m)?)?;
    m.add_function(wrap_pyfunction!(get_window_rect, m)?)?;
    Ok(())
}
