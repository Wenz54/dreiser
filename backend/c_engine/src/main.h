/**
 * DRAIZER V2.0 - Main Engine Header
 * Public API for engine components
 */

#ifndef MAIN_H
#define MAIN_H

/**
 * Notify main loop that new market data has arrived
 * This signals the condition variable to wake up the main processing loop
 * 
 * Thread-safe: Can be called from any WebSocket processing thread
 */
void notify_new_data(void);

#endif // MAIN_H










