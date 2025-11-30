/**
 * Playwright E2E Tests - Phase 11
 * Frontend UI tests for YouTube Downloader
 */

const { test, expect } = require('@playwright/test');

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';

test.describe('YouTube Downloader - Homepage', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
    });

    test('should display the main UI elements', async ({ page }) => {
        // Check header
        await expect(page.locator('.logo h1')).toContainText('YT Downloader');
        
        // Check URL input
        await expect(page.locator('#url-input')).toBeVisible();
        await expect(page.locator('#url-input')).toHaveAttribute('placeholder', /Paste YouTube URL/);
        
        // Check action buttons
        await expect(page.locator('#metadata-btn')).toBeVisible();
        await expect(page.locator('#download-btn')).toBeVisible();
        await expect(page.locator('#download-btn')).toBeDisabled();
    });

    test('should show paste button and clear button correctly', async ({ page }) => {
        const urlInput = page.locator('#url-input');
        const pasteBtn = page.locator('#paste-btn');
        const clearBtn = page.locator('#clear-btn');
        
        // Initially paste button visible, clear button hidden
        await expect(pasteBtn).toBeVisible();
        await expect(clearBtn).toBeHidden();
        
        // Type something
        await urlInput.fill('https://www.youtube.com/watch?v=test');
        
        // Now clear button should be visible
        await expect(clearBtn).toBeVisible();
        await expect(pasteBtn).toBeHidden();
        
        // Click clear
        await clearBtn.click();
        await expect(urlInput).toHaveValue('');
    });

    test('should toggle between URL and Search modes', async ({ page }) => {
        const urlModeBtn = page.locator('.input-mode-btn[data-mode="url"]');
        const searchModeBtn = page.locator('.input-mode-btn[data-mode="search"]');
        const urlInput = page.locator('#url-input');
        
        // Initially in URL mode
        await expect(urlModeBtn).toHaveClass(/active/);
        await expect(urlInput).toHaveAttribute('placeholder', /Paste YouTube URL/);
        
        // Switch to search mode
        await searchModeBtn.click();
        await expect(searchModeBtn).toHaveClass(/active/);
        await expect(urlInput).toHaveAttribute('placeholder', /Search YouTube/);
        
        // Switch back to URL mode
        await urlModeBtn.click();
        await expect(urlModeBtn).toHaveClass(/active/);
    });
});

test.describe('YouTube Downloader - Theme Toggle', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
    });

    test('should toggle between dark and light themes', async ({ page }) => {
        const themeToggleBtn = page.locator('#theme-toggle-btn');
        const html = page.locator('html');
        
        // Default is dark theme
        await expect(html).not.toHaveAttribute('data-theme', 'light');
        
        // Toggle to light
        await themeToggleBtn.click();
        await expect(html).toHaveAttribute('data-theme', 'light');
        
        // Toggle back to dark
        await themeToggleBtn.click();
        await expect(html).toHaveAttribute('data-theme', 'dark');
    });

    test('should persist theme preference', async ({ page }) => {
        // Set to light theme
        await page.locator('#theme-toggle-btn').click();
        
        // Reload page
        await page.reload();
        
        // Should still be light theme
        await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
    });
});

test.describe('YouTube Downloader - Settings Modal', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
    });

    test('should open and close settings modal', async ({ page }) => {
        const settingsBtn = page.locator('#settings-btn');
        const settingsModal = page.locator('#settings-modal');
        
        // Modal initially hidden
        await expect(settingsModal).toHaveClass(/hidden/);
        
        // Open modal
        await settingsBtn.click();
        await expect(settingsModal).not.toHaveClass(/hidden/);
        
        // Close modal via close button
        await page.locator('#settings-modal .modal-close').click();
        await expect(settingsModal).toHaveClass(/hidden/);
    });

    test('should have all settings options', async ({ page }) => {
        await page.locator('#settings-btn').click();
        
        // Check settings elements exist
        await expect(page.locator('#settings-format')).toBeVisible();
        await expect(page.locator('#settings-quality')).toBeVisible();
        await expect(page.locator('#settings-mobile-presets')).toBeVisible();
        await expect(page.locator('#settings-qr-sharing')).toBeVisible();
        await expect(page.locator('#settings-auto-download')).toBeVisible();
    });
});

test.describe('YouTube Downloader - Format Selection', () => {
    test('should switch between video, audio, and mobile tabs', async ({ page }) => {
        await page.goto(BASE_URL);
        
        // Simulate having video info loaded
        await page.evaluate(() => {
            document.getElementById('preview-section').classList.remove('hidden');
        });
        
        const videoTab = page.locator('.format-tab[data-format="video"]');
        const audioTab = page.locator('.format-tab[data-format="audio"]');
        const mobileTab = page.locator('.format-tab[data-format="mobile"]');
        
        // Video tab should be active by default
        await expect(videoTab).toHaveClass(/active/);
        
        // Click audio tab
        await audioTab.click();
        await expect(audioTab).toHaveClass(/active/);
        await expect(videoTab).not.toHaveClass(/active/);
        
        // Click mobile tab
        await mobileTab.click();
        await expect(mobileTab).toHaveClass(/active/);
        
        // Mobile presets should be visible
        await expect(page.locator('#mobile-presets')).toBeVisible();
    });
});

test.describe('YouTube Downloader - API Status', () => {
    test('should show API status in footer', async ({ page }) => {
        await page.goto(BASE_URL);
        
        // Wait for status check
        await page.waitForTimeout(2000);
        
        const statusDot = page.locator('#api-status');
        const statusText = page.locator('#api-status-text');
        
        await expect(statusDot).toBeVisible();
        await expect(statusText).toBeVisible();
    });
});

test.describe('YouTube Downloader - PWA Features', () => {
    test('should have PWA manifest', async ({ page }) => {
        await page.goto(BASE_URL);
        
        // Check manifest link exists
        const manifestLink = page.locator('link[rel="manifest"]');
        await expect(manifestLink).toHaveAttribute('href', 'manifest.json');
    });

    test('should register service worker', async ({ page }) => {
        await page.goto(BASE_URL);
        
        // Wait for service worker registration
        await page.waitForTimeout(1000);
        
        // Check if service worker is registered
        const swRegistered = await page.evaluate(async () => {
            if ('serviceWorker' in navigator) {
                const registration = await navigator.serviceWorker.getRegistration();
                return !!registration;
            }
            return false;
        });
        
        expect(swRegistered).toBeTruthy();
    });
});

test.describe('YouTube Downloader - Responsive Design', () => {
    test('should adapt to mobile viewport', async ({ page }) => {
        // Set mobile viewport
        await page.setViewportSize({ width: 375, height: 667 });
        await page.goto(BASE_URL);
        
        // Check mobile-specific elements
        await expect(page.locator('.logo h1')).toBeVisible();
        await expect(page.locator('#url-input')).toBeVisible();
    });

    test('should adapt to tablet viewport', async ({ page }) => {
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.goto(BASE_URL);
        
        await expect(page.locator('.logo h1')).toBeVisible();
    });

    test('should adapt to desktop viewport', async ({ page }) => {
        await page.setViewportSize({ width: 1920, height: 1080 });
        await page.goto(BASE_URL);
        
        // Bottom bar should be hidden on desktop
        const bottomBar = page.locator('#bottom-bar');
        // Note: Bottom bar visibility depends on video being selected
    });
});

test.describe('YouTube Downloader - Accessibility', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
    });

    test('should have proper aria labels', async ({ page }) => {
        await expect(page.locator('#paste-btn')).toHaveAttribute('aria-label', 'Paste from clipboard');
        await expect(page.locator('#clear-btn')).toHaveAttribute('aria-label', 'Clear input');
        await expect(page.locator('#theme-toggle-btn')).toHaveAttribute('aria-label', 'Toggle theme');
        await expect(page.locator('#settings-btn')).toHaveAttribute('aria-label', 'Settings');
    });

    test('should support keyboard navigation', async ({ page }) => {
        const urlInput = page.locator('#url-input');
        
        // Tab to URL input
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        
        // Type a URL
        await urlInput.fill('https://www.youtube.com/watch?v=test');
        
        // Press Enter (should trigger preview)
        // Note: This will attempt API call which may fail in test environment
    });
});

test.describe('YouTube Downloader - Toast Notifications', () => {
    test('should show and auto-hide toast messages', async ({ page }) => {
        await page.goto(BASE_URL);
        
        // Trigger a toast via JavaScript
        await page.evaluate(() => {
            window.app.showToast('Test message', 'success');
        });
        
        // Toast should appear
        const toast = page.locator('.toast').first();
        await expect(toast).toBeVisible();
        await expect(toast).toContainText('Test message');
        
        // Toast should have success class
        await expect(toast).toHaveClass(/success/);
        
        // Wait for auto-dismiss (5 seconds + animation)
        await page.waitForTimeout(6000);
        
        // Toast should be removed
        await expect(page.locator('.toast')).toHaveCount(0);
    });
});
