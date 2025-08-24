// overlay.js - Visual Overlay System
class WebAutomationOverlay {
    constructor() {
        this.overlayElements = new Map();
        this.currentAction = null;
        this.sessionId = this.generateSessionId();
        this.initStyles();
        this.setupMessageListener();
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    initStyles() {
        // Inject dynamic styles for overlay elements
        if (!document.getElementById('wa-overlay-styles')) {
            const style = document.createElement('style');
            style.id = 'wa-overlay-styles';
            style.textContent = `
                .wa-overlay-highlight {
                    position: absolute;
                    pointer-events: none;
                    z-index: 999999;
                    transition: all 0.3s ease;
                    border-radius: 4px;
                    animation: wa-pulse 1.5s infinite;
                }

                @keyframes wa-pulse {
                    0% { transform: scale(1); opacity: 0.7; }
                    50% { transform: scale(1.05); opacity: 0.9; }
                    100% { transform: scale(1); opacity: 0.7; }
                }

                .wa-overlay-tooltip {
                    position: absolute;
                    background: rgba(0, 0, 0, 0.9);
                    color: white;
                    padding: 8px 12px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-family: system-ui, -apple-system, sans-serif;
                    z-index: 999999;
                    pointer-events: none;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                    max-width: 250px;
                    line-height: 1.4;
                }

                .wa-overlay-tooltip::after {
                    content: '';
                    position: absolute;
                    bottom: -8px;
                    left: 50%;
                    transform: translateX(-50%);
                    border-left: 8px solid transparent;
                    border-right: 8px solid transparent;
                    border-top: 8px solid rgba(0, 0, 0, 0.9);
                }

                .wa-color-red { border: 3px solid #ff4444; background: rgba(255, 68, 68, 0.2); }
                .wa-color-blue { border: 3px solid #4444ff; background: rgba(68, 68, 255, 0.2); }
                .wa-color-green { border: 3px solid #44ff44; background: rgba(68, 255, 68, 0.2); }
                .wa-color-yellow { border: 3px solid #ffff44; background: rgba(255, 255, 68, 0.2); }
                .wa-color-purple { border: 3px solid #ff44ff; background: rgba(255, 68, 255, 0.2); }
            `;
            document.head.appendChild(style);
        }
    }

    setupMessageListener() {
        // Listen for actions from background script
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.type === 'EXECUTE_ACTION') {
                this.executeAction(request.action)
                    .then(result => sendResponse({ success: true, result }))
                    .catch(error => sendResponse({ success: false, error: error.message }));
                return true; // Keep channel open for async response
            }

            if (request.type === 'CLEAR_OVERLAYS') {
                this.clearAllOverlays();
                sendResponse({ success: true });
            }

            if (request.type === 'GET_PAGE_STRUCTURE') {
                const structure = this.analyzeDOMStructure();
                sendResponse({ success: true, structure });
            }
        });
    }

    async executeAction(action) {
        console.log('Executing action:', action);

        const element = await this.findElement(action.target);
        if (!element) {
            throw new Error(`Element not found: ${JSON.stringify(action.target)}`);
        }

        // Apply overlay if specified
        if (action.overlay) {
            this.highlightElement(element, action.overlay);
        }

        // Apply delay if specified
        if (action.options?.delay) {
            await this.delay(action.options.delay);
        }

        // Execute action based on type
        switch (action.type) {
            case 'click':
                await this.clickElement(element);
                break;
            case 'type':
                await this.typeInElement(element, action.value);
                break;
            case 'select':
                await this.selectOption(element, action.value);
                break;
            case 'hover':
                await this.hoverElement(element);
                break;
            case 'scroll':
                await this.scrollToElement(element);
                break;
            case 'wait':
                await this.waitForCondition(action);
                break;
            case 'screenshot':
                return await this.captureScreenshot(element);
            default:
                throw new Error(`Unknown action type: ${action.type}`);
        }

        return { type: action.type, target: action.target, timestamp: Date.now() };
    }

    async findElement(target) {
        // Try multiple strategies to find element
        let element = null;

        // Strategy 1: CSS Selector
        if (target.selector) {
            element = document.querySelector(target.selector);
        }

        // Strategy 2: Text matching
        if (!element && target.text) {
            element = this.findByText(target.text);
        }

        // Strategy 3: Position
        if (!element && target.position) {
            element = document.elementFromPoint(target.position.x, target.position.y);
        }

        return element;
    }

    findByText(text) {
        const xpath = `//*[contains(text(), '${text}')]`;
        const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
        return result.singleNodeValue;
    }

    highlightElement(element, overlay) {
        const rect = element.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

        // Create highlight overlay
        const highlight = document.createElement('div');
        highlight.className = `wa-overlay-highlight wa-color-${overlay.color || 'blue'}`;
        highlight.style.left = `${rect.left + scrollLeft}px`;
        highlight.style.top = `${rect.top + scrollTop}px`;
        highlight.style.width = `${rect.width}px`;
        highlight.style.height = `${rect.height}px`;

        document.body.appendChild(highlight);
        this.overlayElements.set(element, highlight);

        // Add tooltip if specified
        if (overlay.label) {
            const tooltip = document.createElement('div');
            tooltip.className = 'wa-overlay-tooltip';
            tooltip.textContent = overlay.label;
            tooltip.style.left = `${rect.left + scrollLeft + rect.width / 2}px`;
            tooltip.style.top = `${rect.top + scrollTop - 50}px`;
            tooltip.style.transform = 'translateX(-50%)';

            document.body.appendChild(tooltip);
            this.overlayElements.set(element + '_tooltip', tooltip);
        }

        // Auto-remove after duration
        if (overlay.duration) {
            setTimeout(() => {
                this.removeOverlay(element);
            }, overlay.duration);
        }
    }

    removeOverlay(element) {
        const highlight = this.overlayElements.get(element);
        const tooltip = this.overlayElements.get(element + '_tooltip');

        if (highlight) {
            highlight.remove();
            this.overlayElements.delete(element);
        }
        if (tooltip) {
            tooltip.remove();
            this.overlayElements.delete(element + '_tooltip');
        }
    }

    clearAllOverlays() {
        this.overlayElements.forEach(overlay => overlay.remove());
        this.overlayElements.clear();
    }

    async clickElement(element) {
        // Scroll into view if needed
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        await this.delay(300);

        // Simulate human-like click
        const event = new MouseEvent('click', {
            view: window,
            bubbles: true,
            cancelable: true,
            buttons: 1
        });
        element.dispatchEvent(event);
    }

    async typeInElement(element, text) {
        element.focus();
        await this.delay(100);

        // Clear existing value
        element.value = '';

        // Type character by character with random delays
        for (const char of text) {
            element.value += char;
            element.dispatchEvent(new Event('input', { bubbles: true }));
            await this.delay(50 + Math.random() * 50); // 50-100ms between keystrokes
        }

        element.dispatchEvent(new Event('change', { bubbles: true }));
    }

    async hoverElement(element) {
        const event = new MouseEvent('mouseover', {
            view: window,
            bubbles: true,
            cancelable: true
        });
        element.dispatchEvent(event);
    }

    async scrollToElement(element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        await this.delay(500);
    }

    analyzeDOMStructure() {
        // Analyze page structure for intelligent element detection
        const structure = {
            forms: [],
            buttons: [],
            inputs: [],
            links: [],
            interactive: []
        };

        // Find all forms
        document.querySelectorAll('form').forEach(form => {
            structure.forms.push({
                id: form.id,
                class: form.className,
                action: form.action,
                method: form.method
            });
        });

        // Find all input elements
        document.querySelectorAll('input, textarea, select').forEach(input => {
            structure.inputs.push({
                type: input.type || input.tagName.toLowerCase(),
                id: input.id,
                name: input.name,
                placeholder: input.placeholder,
                label: this.findLabelForInput(input)
            });
        });

        // Find all buttons
        document.querySelectorAll('button, input[type="submit"], input[type="button"]').forEach(button => {
            structure.buttons.push({
                text: button.textContent || button.value,
                type: button.type,
                id: button.id,
                class: button.className
            });
        });

        return structure;
    }

    findLabelForInput(input) {
        // Try to find associated label
        if (input.id) {
            const label = document.querySelector(`label[for="${input.id}"]`);
            if (label) return label.textContent;
        }

        // Check if input is inside a label
        const parentLabel = input.closest('label');
        if (parentLabel) return parentLabel.textContent;

        return null;
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize overlay system
const waOverlay = new WebAutomationOverlay();
console.log('Web Automation Overlay initialized:', waOverlay.sessionId);
