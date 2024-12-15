import os
import json
from dotenv import load_dotenv
from openai import OpenAI

def load_menu(menu_file='menu.json'):
    try:
        with open(menu_file, 'r') as f:
            menu = json.load(f)
        return menu
    except FileNotFoundError:
        print(f"Error: {menu_file} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: {menu_file} contains invalid JSON.")
        return None

def find_item_by_name(item_name, menu):
    for category, items in menu['categories'].items():
        for item in items:
            if item['name'].lower() == item_name.lower():
                return item
    return None

def find_item_by_id(item_id, menu):
    for category, items in menu['categories'].items():
        for item in items:
            if item['id'] == item_id:
                return item
    return None

def extract_item_name(user_input, menu):
    tokens = user_input.lower().split()
    for category, items in menu['categories'].items():
        for item in items:
            if item['name'].lower() in user_input.lower():
                print(f"Debug: Detected item name: {item['name']}")  # Debugging statement
                return item['name']
    return None

def get_agent_response(conversation_history, user_input, menu, user_order, client):
    system_prompt = "You are a helpful restaurant ordering assistant. Here is the menu:\n"
    for category, items in menu['categories'].items():
        system_prompt += f"{category.capitalize()}:\n"
        for item in items:
            system_prompt += f" - {item['name']} (${item['price']})\n"

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    for turn in conversation_history:
        messages.append({"role": turn['role'], "content": turn['message']})

    messages.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=150,
            temperature=0.7,
            n=1,
            stop=None
        )
        agent_message = response.choices[0].message.content.strip()

        if any(keyword in user_input.lower() for keyword in ["i would like", "i want", "add", "order"]):
            item_name = extract_item_name(user_input, menu)
            if item_name:
                item = find_item_by_name(item_name, menu)
                if item:
                    user_order.append(item['id'])
                    print(f"Debug: Added item ID to order: {item['id']}")  # Debugging statement
                    agent_message += f" I've added the {item['name']} to your order."
                else:
                    agent_message += " Sorry, I couldn't find that item on the menu."
            else:
                agent_message += " Could you please specify the item you'd like to order?"

        return agent_message
    except Exception as e:
        print(f"Error communicating with OpenAI API: {e}")
        return "I'm sorry, I'm having trouble processing your request right now."

def main():
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        print("Error: OPENAI_API_KEY not found. Please set it in the .env file.")
        return

    client = OpenAI(api_key=openai_api_key)

    print("Restaurant Chatbot is starting...")

    menu = load_menu()
    if not menu:
        return

    print("\nHere are our available categories:")
    for category in menu['categories']:
        print(f"- {category.capitalize()}")

    conversation_history = []
    user_order = []

    initial_message = "Hey, how are you doing today? What would you like to have?"
    print(f"Agent: {initial_message}")
    conversation_history.append({"role": "assistant", "message": initial_message})

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Agent: Is there anything else you need help with before I go off?")
            confirmation = input("You: ")
            if confirmation.lower() in ['no', 'nothing', 'go ahead', 'bye']:
                if user_order:
                    print("Agent:", user_order)
                else:
                    print("Agent: -1")
                break
            else:
                print("Agent: Sure, let me know how I can assist you further!")
                continue

        conversation_history.append({"role": "user", "message": user_input})

        agent_response = get_agent_response(conversation_history, user_input, menu, user_order, client)
        print(f"Agent: {agent_response}")

        conversation_history.append({"role": "assistant", "message": agent_response})

if __name__ == "__main__":
    main()
