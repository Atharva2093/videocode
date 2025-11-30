// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright Configuration - Phase 11
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
    testDir: './frontend/tests',
    
    // Run tests in parallel
    fullyParallel: true,
    
    // Fail the build on CI if test.only was left
    forbidOnly: !!process.env.CI,
    
    // Retry on CI only
    retries: process.env.CI ? 2 : 0,
    
    // Opt out of parallel tests on CI
    workers: process.env.CI ? 1 : undefined,
    
    // Reporter
    reporter: [
        ['list'],
        ['html', { outputFolder: 'playwright-report' }],
        ['junit', { outputFile: 'test-results/junit.xml' }]
    ],
    
    // Shared settings for all the projects below
    use: {
        // Base URL
        baseURL: process.env.BASE_URL || 'http://localhost:8000',
        
        // Collect trace when retrying the failed test
        trace: 'on-first-retry',
        
        // Screenshot on failure
        screenshot: 'only-on-failure',
        
        // Video on failure
        video: 'on-first-retry',
    },

    // Configure projects for major browsers
    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },

        {
            name: 'firefox',
            use: { ...devices['Desktop Firefox'] },
        },

        {
            name: 'webkit',
            use: { ...devices['Desktop Safari'] },
        },

        // Test against mobile viewports
        {
            name: 'Mobile Chrome',
            use: { ...devices['Pixel 5'] },
        },
        
        {
            name: 'Mobile Safari',
            use: { ...devices['iPhone 12'] },
        },

        // Tablet viewport
        {
            name: 'Tablet',
            use: { ...devices['iPad (gen 7)'] },
        },
    ],

    // Run your local dev server before starting the tests
    webServer: {
        command: 'cd backend && uvicorn main:app --host 0.0.0.0 --port 8000',
        url: 'http://localhost:8000',
        reuseExistingServer: !process.env.CI,
        timeout: 120 * 1000,
    },
});
