def check_module_health(module_name):
    try:
        # Try to import the module dynamically
        module = importlib.import_module(f"src.modules.{module_name}")

        # Check for necessary components (like the 'BOT' object)
        if hasattr(module, 'BOT'):
            bot_status = "✅ BOT found"
        else:
            return False, f"❌ {module_name} does not contain a 'BOT' object."

        # Test some of the critical functions or classes in the module
        # Example: Checking if specific functions exist or are callable.
        required_functions = ['update_admins', 'handle_chat_action']  # List critical functions to check
        missing_functions = []
        for func in required_functions:
            if not hasattr(module, func) or not callable(getattr(module, func)):
                missing_functions.append(func)

        if missing_functions:
            return False, f"❌ {module_name} is missing functions: {', '.join(missing_functions)}."

        # Optionally, you can call a function to test the module's behavior.
        # E.g., check if a bot can send a message or execute a simple task.
        if hasattr(module, 'BOT'):
            try:
                # Check if the bot can send a test message
                test_message = "Test message for health check"
                # Example: You can check if this works in any chat or specific chat
                # You can add more complex logic here to ensure the module works as expected
                BOT.send_message("test_channel", test_message)  # Or use any valid chat ID
                return True, f"✅ {module_name} loaded and working properly."
            except Exception as e:
                return False, f"❌ {module_name} failed to send a test message: {str(e)}"

        return True, f"✅ {module_name} is operational."

    except Exception as e:
        return False, f"❌ Failed to load {module_name}: {str(e)}"
