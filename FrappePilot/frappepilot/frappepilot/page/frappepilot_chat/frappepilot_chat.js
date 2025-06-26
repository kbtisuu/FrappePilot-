frappe.pages['frappepilot-chat'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'FrappePilot Chat',
		single_column: true
	});
	
	// Initialize the chat interface
	new FrappePilotChat(page);
};

class FrappePilotChat {
	constructor(page) {
		this.page = page;
		this.wrapper = page.main;
		this.setup_chat();
		this.bind_events();
		this.check_status();
	}
	
	setup_chat() {
		// Load the chat HTML
		$(this.wrapper).html(frappe.render_template('frappepilot_chat'));
		
		// Initialize elements
		this.chat_messages = this.wrapper.find('#chat-messages');
		this.chat_input = this.wrapper.find('#chat-input');
		this.send_button = this.wrapper.find('#send-button');
		this.status_indicator = this.wrapper.find('#status-indicator');
		this.status_text = this.wrapper.find('#status-text');
		this.chat_typing = this.wrapper.find('#chat-typing');
		this.chat_suggestions = this.wrapper.find('#chat-suggestions');
		
		// Load conversation history
		this.load_conversation_history();
	}
	
	bind_events() {
		// Send button click
		this.send_button.on('click', () => {
			this.send_message();
		});
		
		// Enter key press
		this.chat_input.on('keypress', (e) => {
			if (e.which === 13) {
				this.send_message();
			}
		});
		
		// Suggestion buttons
		this.chat_suggestions.on('click', '.suggestion-btn', (e) => {
			const suggestion = $(e.target).data('suggestion');
			this.chat_input.val(suggestion);
			this.send_message();
		});
		
		// Auto-resize chat messages
		$(window).on('resize', () => {
			this.scroll_to_bottom();
		});
	}
	
	async check_status() {
		try {
			const response = await frappe.call({
				method: 'frappepilot.api.chat.check_status'
			});
			
			if (response.message.status === 'online') {
				this.update_status('online', 'Online');
			} else {
				this.update_status('error', 'Offline');
			}
		} catch (error) {
			this.update_status('error', 'Connection Error');
		}
	}
	
	update_status(status, text) {
		this.status_indicator.removeClass('connecting error').addClass(status);
		this.status_text.text(text);
	}
	
	async send_message() {
		const message = this.chat_input.val().trim();
		if (!message) return;
		
		// Clear input
		this.chat_input.val('');
		
		// Add user message to chat
		this.add_message(message, 'user');
		
		// Show typing indicator
		this.show_typing();
		
		try {
			// Send message to backend
			const response = await frappe.call({
				method: 'frappepilot.api.chat.process_message',
				args: {
					message: message
				}
			});
			
			// Hide typing indicator
			this.hide_typing();
			
			if (response.message.success) {
				// Add assistant response
				this.add_message(response.message.response, 'assistant');
				
				// Show success if action was executed
				if (response.message.action_executed) {
					this.show_notification('Action executed successfully', 'success');
				}
			} else {
				// Add error response
				this.add_message(response.message.error || 'Sorry, I encountered an error processing your request.', 'assistant', true);
				this.show_notification(response.message.error || 'Error processing message', 'error');
			}
		} catch (error) {
			this.hide_typing();
			this.add_message('Sorry, I\'m having trouble connecting. Please try again.', 'assistant', true);
			this.show_notification('Connection error', 'error');
		}
	}
	
	add_message(content, sender, is_error = false) {
		const time = frappe.datetime.now_time();
		const avatar_icon = sender === 'user' ? 'fa-user' : 'fa-robot';
		const message_class = sender === 'user' ? 'user-message' : 'assistant-message';
		const error_class = is_error ? 'error-message' : '';
		
		const message_html = `
			<div class="message ${message_class}">
				<div class="message-avatar">
					<i class="fa ${avatar_icon}"></i>
				</div>
				<div class="message-content ${error_class}">
					<p>${content}</p>
					<small class="message-time">${time}</small>
				</div>
			</div>
		`;
		
		this.chat_messages.append(message_html);
		this.scroll_to_bottom();
	}
	
	show_typing() {
		this.chat_typing.show();
		this.scroll_to_bottom();
	}
	
	hide_typing() {
		this.chat_typing.hide();
	}
	
	scroll_to_bottom() {
		this.chat_messages.scrollTop(this.chat_messages[0].scrollHeight);
	}
	
	show_notification(message, type) {
		frappe.show_alert({
			message: message,
			indicator: type === 'success' ? 'green' : 'red'
		});
	}
	
	async load_conversation_history() {
		try {
			const response = await frappe.call({
				method: 'frappepilot.api.chat.get_conversation_history',
				args: {
					limit: 10
				}
			});
			
			if (response.message && response.message.length > 0) {
				// Clear welcome message
				this.chat_messages.empty();
				
				// Add historical messages
				response.message.forEach(log => {
					this.add_message(log.user_input, 'user');
					if (log.assistant_response) {
						this.add_message(log.assistant_response, 'assistant');
					}
				});
			}
		} catch (error) {
			console.log('Could not load conversation history:', error);
		}
	}
}

