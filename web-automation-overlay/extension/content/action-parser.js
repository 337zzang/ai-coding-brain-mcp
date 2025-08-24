// action-parser.js - Action Protocol Parser and Validator
class ActionParser {
    constructor() {
        this.actionQueue = [];
        this.currentIndex = 0;
        this.isExecuting = false;
    }

    validateAction(action) {
        const errors = [];

        // Validate action type
        const validTypes = ['click', 'type', 'select', 'wait', 'scroll', 'hover', 'screenshot'];
        if (!validTypes.includes(action.type)) {
            errors.push(`Invalid action type: ${action.type}`);
        }

        // Validate target
        if (!action.target) {
            errors.push('Action must have a target');
        } else {
            const hasValidTarget = action.target.selector || action.target.text || action.target.position;
            if (!hasValidTarget) {
                errors.push('Target must have selector, text, or position');
            }
        }

        // Validate type-specific requirements
        if (action.type === 'type' && !action.value) {
            errors.push('Type action must have a value');
        }

        return errors.length === 0 ? { valid: true } : { valid: false, errors };
    }

    parseActionSequence(jsonString) {
        try {
            const sequence = JSON.parse(jsonString);

            // Validate sequence structure
            if (!sequence.version || !sequence.session_id || !sequence.actions) {
                throw new Error('Invalid action sequence structure');
            }

            // Validate each action
            const validatedActions = sequence.actions.map((action, index) => {
                const validation = this.validateAction(action);
                if (!validation.valid) {
                    throw new Error(`Action ${index}: ${validation.errors.join(', ')}`);
                }
                return action;
            });

            return {
                success: true,
                sequence: {
                    ...sequence,
                    actions: validatedActions
                }
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    async executeSequence(sequence) {
        this.actionQueue = sequence.actions;
        this.currentIndex = 0;
        this.isExecuting = true;

        const results = [];

        for (let i = 0; i < this.actionQueue.length; i++) {
            if (!this.isExecuting) break;

            const action = this.actionQueue[i];
            this.currentIndex = i;

            try {
                // Send action to overlay system
                const result = await this.sendActionToOverlay(action);
                results.push({ success: true, action, result });

                // Notify progress
                this.notifyProgress(i + 1, this.actionQueue.length);
            } catch (error) {
                results.push({ success: false, action, error: error.message });

                // Check if should continue on error
                if (!action.options?.continueOnError) {
                    this.isExecuting = false;
                    break;
                }
            }
        }

        this.isExecuting = false;
        return results;
    }

    sendActionToOverlay(action) {
        return new Promise((resolve, reject) => {
            chrome.runtime.sendMessage(
                { type: 'EXECUTE_ACTION', action },
                response => {
                    if (response.success) {
                        resolve(response.result);
                    } else {
                        reject(new Error(response.error));
                    }
                }
            );
        });
    }

    notifyProgress(current, total) {
        chrome.runtime.sendMessage({
            type: 'PROGRESS_UPDATE',
            progress: {
                current,
                total,
                percentage: Math.round((current / total) * 100)
            }
        });
    }

    stopExecution() {
        this.isExecuting = false;
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ActionParser;
}
