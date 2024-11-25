import requests # type: ignore
import logging

# Logging setup
logging.basicConfig(level=logging.INFO, filename="contract_score_bot.log", format='%(asctime)s - %(message)s')

# Constants
DEX_API_URL = "https://api.dexscreener.com/latest/dex/tokens"
SOL_SNIFFER_BASE_URL = "https://solsniffer.com/?q="
TELEGRAM_API_BASE = "https://api.telegram.org/bot"

# Replace with your Telegram bot token and chat ID
TELEGRAM_BOT_TOKEN = "7997314066:AAEVWmfAZa_nlhTK-aq38eNYQFT8QI2um-g"
TELEGRAM_CHAT_ID = "@NickTsalyn"


def fetch_tokens_from_dex():
    """Fetch Solana tokens from the DEX Screener API."""
    try:
        response = requests.get(DEX_API_URL)
        response.raise_for_status()
        data = response.json()
        
        # Filter for Solana tokens (adjust filtering as needed based on API response structure)
        solana_tokens = [
            {"ticker": token["symbol"], "contract": token["address"]}
            for token in data["pairs"]
            if token["chainId"] == "sol"  # Check for Solana chain
        ]
        return solana_tokens
    except Exception as e:
        logging.error(f"Error fetching data from DEX Screener API: {e}")
        return []


def get_contract_score(contract):
    """Fetch contract score from solsniffer.com."""
    try:
        url = f"{SOL_SNIFFER_BASE_URL}{contract}"
        response = requests.get(url)
        response.raise_for_status()
        # Parse the score (adjust this based on the actual page structure)
        # Use BeautifulSoup if needed for complex parsing
        if "score" in response.text:
            score = int(response.text.split("score:")[1].split()[0])  # Example parsing logic
            return score
    except Exception as e:
        logging.error(f"Error fetching contract score for {contract}: {e}")
    return None


def filter_low_score_contracts(tokens, threshold=85):
    """Filter contracts with scores below the threshold."""
    low_score_contracts = []

    for token in tokens:
        contract = token["contract"]
        ticker = token["ticker"]
        score = get_contract_score(contract)
        if score is not None and score < threshold:
            low_score_contracts.append({
                "ticker": ticker,
                "contract": contract,
                "score": score
            })
    return low_score_contracts


def send_telegram_notification(low_score_contracts):
    """Send Telegram notification for low-score contracts."""
    url = f"{TELEGRAM_API_BASE}{TELEGRAM_BOT_TOKEN}/sendMessage"
    message = "⚠️ Low Contract Scores Detected:\n\n"
    for contract in low_score_contracts:
        message += f"Ticker: {contract['ticker']}, Contract: {contract['contract']}, Score: {contract['score']}\n"

    try:
        response = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        if response.status_code == 200:
            print("Telegram notification sent successfully.")
        else:
            logging.error(f"Failed to send Telegram notification: {response.text}")
    except Exception as e:
        logging.error(f"Error sending Telegram notification: {e}")


def log_low_scores(low_score_contracts):
    """Log low-score contracts to a file."""
    for contract in low_score_contracts:
        logging.info(f"Low Score: Ticker={contract['ticker']}, Contract={contract['contract']}, Score={contract['score']}")


def main():
    """Main function to run the bot."""
    # Step 1: Fetch tokens dynamically from DEX Screener API
    tokens = fetch_tokens_from_dex()

    if not tokens:
        print("No tokens fetched from DEX Screener API.")
        return

    # Step 2: Check contract scores
    low_score_contracts = filter_low_score_contracts(tokens)

    # Step 3: Notify if any low scores found
    if low_score_contracts:
        send_telegram_notification(low_score_contracts)
        log_low_scores(low_score_contracts)
    else:
        print("No low-score contracts found.")


if __name__ == "__main__":
    main()