// background.js - Service Worker for Extension Communication
class BackgroundService {
    constructor() {
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.setupListeners();
        this.connectWebSocket();
    }

    setupListeners() {
        // Listen for messages from content scripts
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            console.log('Background received message:', request.type);

            switch (request.type) {
                case 'CONNECT_WEBSOCKET':
                    this.connectWebSocket();
                    sendResponse({ success: true });
                    break;

                case 'SEND_TO_AI':
                    this.sendToAI(request.data)
                        .then(response => sendResponse({ success: true, response }))
                        .catch(error => sendResponse({ success: false, error: error.message }));
                    return true; // Keep channel open

                case 'GET_CONNECTION_STATUS':
                    sendResponse({
                        connected: this.websocket?.readyState === WebSocket.OPEN,
                        url: this.websocket?.url
                    });
                    break;

                default:
                    // Forward to active tab
                    this.forwardToActiveTab(request, sendResponse);
                    return true;
            }
        });

        // Listen for extension icon click
        chrome.action.onClicked.addListener((tab) => {
            chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: () => {
                    console.log('Web Automation Overlay activated');
                    // Trigger overlay initialization if needed
                }
            });
        });
    }

    connectWebSocket() {
        const wsUrl = 'ws://localhost:8765'; // Default WebSocket server URL

        try {
            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                console.log('WebSocket connected to:', wsUrl);
                this.reconnectAttempts = 0;
                this.notifyConnectionStatus(true);
            };

            this.websocket.onmessage = (event) => {
                console.log('WebSocket message received:', event.data);
                this.handleWebSocketMessage(event.data);
            };

            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.notifyConnectionStatus(false);
                this.attemptReconnect();
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
            setTimeout(() => this.connectWebSocket(), delay);
        }
    }

    async handleWebSocketMessage(data) {
        try {
            const message = JSON.parse(data);

            if (message.type === 'ACTION_SEQUENCE') {
                // Forward action sequence to active tab
                const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
                if (tab) {
                    chrome.tabs.sendMessage(tab.id, {
                        type: 'EXECUTE_SEQUENCE',
                        sequence: message.sequence
                    });
                }
            }
        } catch (error) {
            console.error('Error handling WebSocket message:', error);
        }
    }

    async sendToAI(data) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            throw new Error('WebSocket not connected');
        }

        return new Promise((resolve, reject) => {
            const messageId = Date.now().toString();

            const responseHandler = (event) => {
                const response = JSON.parse(event.data);
                if (response.messageId === messageId) {
                    this.websocket.removeEventListener('message', responseHandler);
                    resolve(response);
                }
            };

            this.websocket.addEventListener('message', responseHandler);

            this.websocket.send(JSON.stringify({
                messageId,
                ...data
            }));

            // Timeout after 30 seconds
            setTimeout(() => {
                this.websocket.removeEventListener('message', responseHandler);
                reject(new Error('Request timeout'));
            }, 30000);
        });
    }

    async forwardToActiveTab(request, sendResponse) {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tab) {
                chrome.tabs.sendMessage(tab.id, request, sendResponse);
            } else {
                sendResponse({ success: false, error: 'No active tab found' });
            }
        } catch (error) {
            sendResponse({ success: false, error: error.message });
        }
    }

    notifyConnectionStatus(connected) {
        // Broadcast connection status to all tabs
        chrome.tabs.query({}, (tabs) => {
            tabs.forEach(tab => {
                chrome.tabs.sendMessage(tab.id, {
                    type: 'WEBSOCKET_STATUS',
                    connected
                }).catch(() => {}); // Ignore errors for tabs without content script
            });
        });
    }
}

// Initialize background service
const backgroundService = new BackgroundService();
console.log('Background service initialized');
