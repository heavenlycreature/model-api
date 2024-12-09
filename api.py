import os
from google.cloud import firestore
from google.oauth2.service_account import Credentials
from flask import Flask, request, jsonify
import tensorflow as tf
import numpy as np
from flask_cors import CORS
import requests
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Flask and Logging Setup
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
load_dotenv()

port = os.getenv('PORT')

# Firestore Initialization
credentials = Credentials.from_service_account_file(
    os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
)
firestore_client = firestore.Client(credentials=credentials,project='capstone-ezmoney-service-app')

# Model Setup
MODEL_URL = os.getenv('MODEL_URL')
LOCAL_MODEL_PATH = "downloaded_model.h5"

# Download model if not present
if not os.path.exists(LOCAL_MODEL_PATH):
    try:
        response = requests.get(MODEL_URL, stream=True)
        with open(LOCAL_MODEL_PATH, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
    except Exception as e:
        raise RuntimeError(f"Failed to download model: {e}")

# Load model
model = tf.keras.models.load_model(LOCAL_MODEL_PATH)

# Category and User Encoding
CATEGORY_ENCODING = {
    "food": 1,
    "transport": 2,
    "entertainment": 3,
    "shopping": 4,
    "Utilitas": 5,
    "Hiburan": 6,
    "Lain-Lain": 7,
    "saving": 8,
    "default": 0
}

# Initialize smoothing
previous_prediction = 0.5
alpha = 0.8

def encode_category(category):
    """Encode category string to numeric value."""
    return CATEGORY_ENCODING.get(category.lower(), CATEGORY_ENCODING['default'])

def encode_user_id(user_id):
    """Convert user ID string to numeric value."""
    try:
        return hash(user_id) % 1000
    except Exception as e:
        logging.error(f"User ID encoding error: {e}")
        return 0

def get_user_savings_info(firestore_client, user_id, month):
    """Retrieve user's savings information from Firestore."""
    try:
        # Navigate to the specific month document in the transactions subcollection
        savings_doc_ref = firestore_client.collection('users').document(user_id) \
            .collection('transactions').document(month)
        
        savings_doc = savings_doc_ref.get()
        
        if not savings_doc.exists:
            logging.warning(f"No savings info found for user {user_id} in month {month}")
            return 0, 2  # Default values
        
        savings_data = savings_doc.to_dict()
        savings_balance = savings_data.get('recommendedSavings', 0)
        total_saving = savings_data.get('savingBalance', 0)
        savings_percentage = savings_data.get('saving', 2)
        
        return savings_balance, savings_percentage, total_saving
    except Exception as e:
        logging.error(f"Savings info retrieval error: {e}")
        return 0, 2  # Default values

def get_transactions_for_month(firestore_client, user_id, month):
    """Retrieve transactions for a specific user and month."""
    try:
        # Path to the records subcollection
        records_ref = firestore_client.collection('users').document(user_id).collection('transactions').document(month).collection('records')
        
        # Query transactions with type 'expenses'
        query = records_ref.where('type', '==', 'expenses')
        transactions = list(query.stream())
        
        if not transactions:
            logging.warning(f"No transactions found for user {user_id} in month {month}")
        
        return transactions
    except Exception as e:
        logging.error(f"Transactions retrieval error: {e}")
        return []
def preprocess_input(user_id, category, amount):
    return (
        encode_user_id(user_id) / 1000, 
        encode_category(category) / 100, 
        np.log1p(amount) / 10  # Log normalization for amount
    )
def smooth_prediction(current_prediction):
    """Apply exponential smoothing to predictions."""
    global previous_prediction
    smoothed = alpha * current_prediction + (1 - alpha) * previous_prediction
    previous_prediction = smoothed
    return np.clip(smoothed, 0, 1)

def check_spending(amount, savings_balance, savings_percentage):
    """Check if spending exceeds savings threshold."""
    limit = savings_balance * (savings_percentage / 100)
    if amount > limit:
        return f"Warning: Spending exceeds {savings_percentage}% of savings."
    return "Spending is within limits."

def generate_enhanced_spending_alert(total_spending, savings_balance, total_saving, savings_percentage, predicted_label):
    """
    Generate a comprehensive and structured JSON response for spending analysis.
    
    Args:
        total_spending (float): Total amount spent
        savings_balance (float): Total savings balance
        savings_percentage (float): Percentage of income saved
        predicted_label (float): Model's prediction score
    
    Returns:
        dict: Structured JSON response with detailed spending analysis
    """
    # Define spending threshold
    SPENDING_THRESHOLD = 0.7

    # Base response structure
    response = {
        "financial_indicators": {
            "total_spending": total_spending,
            "savings_balance": savings_balance,
            "total_saving": total_saving,
            "savings_percentage": savings_percentage,
            "prediction_score": float(predicted_label)
        },
        "spending_status": {
            "code": "",
            "level": "",
            "description": ""
        },
        "alert": {
            "type": "",
            "message": "",
            "recommendations": []
        },
        "risk_assessment": {
            "spending_risk_level": "",
            "financial_health_index": 0.0
        }
    }

    # High Spending Scenario (Spending exceeds savings)
    if total_spending > savings_balance:
        spending_difference = total_spending - savings_balance
        
        response.update({
            "spending_status": {
                "code": "CRITICAL_OVERSPENDING",
                "level": "HIGH RISK",
                "description": "Pengeluaran Melebihi Tabungan"
            },
            "alert": {
                "type": "URGENT",
                "message": f"""
🚨 PERINGATAN KEUANGAN KRITIS 🚨

Pengeluaran Anda telah MELEBIHI total tabungan.

Detail Keuangan:
• Total Tabungan: Rp {total_saving:,.2f}
• Total Pengeluaran: Rp {total_spending:,.2f}
• Selisih: Rp {spending_difference:,.2f}

Segera lakukan tindakan untuk mengendalikan keuangan Anda!""",
                "recommendations": [
                    "Kurangi pengeluaran tidak perlu",
                    "Buat prioritas kebutuhan vs keinginan",
                    "Pertimbangkan sumber pendapatan tambahan",
                    "Buat catatan keuangan harian"
                ]
            },
            "risk_assessment": {
                "spending_risk_level": "CRITICAL",
                "financial_health_index": 0.2  # Very low financial health
            }
        })

    # High Spending Prediction Scenario
    elif predicted_label > SPENDING_THRESHOLD:
        spending_ratio = (total_spending / savings_balance) * 100
        
        response.update({
            "spending_status": {
                "code": "POTENTIAL_OVERSPENDING",
                "level": "MODERATE RISK",
                "description": "Pola Pengeluaran Berisiko"
            },
            "alert": {
                "type": "WARNING",
                "message": f"""
⚠️ PERINGATAN POLA PENGELUARAN ⚠️

Pola pengeluaran Anda menunjukkan risiko keuangan.

Detail:
• Rasio Pengeluaran: {spending_ratio:.2f}%
• Total Tabungan: Rp {total_saving:,.2f}
• Total Pengeluaran: Rp {total_spending:,.2f}

Perhatian diperlukan untuk mencegah risiko keuangan!""",
                "recommendations": [
                    "Evaluasi pola pengeluaran",
                    "Buat anggaran bulanan yang ketat",
                    "Identifikasi area penghematan",
                    "Pertimbangkan sumber pendapatan tambahan"
                ]
            },
            "risk_assessment": {
                "spending_risk_level": "MODERATE",
                "financial_health_index": 0.5  # Moderate financial health
            }
        })

    # Normal Spending Scenario
    else:
        spending_ratio = (total_spending / savings_balance) * 100
        
        response.update({
            "spending_status": {
                "code": "HEALTHY_SPENDING",
                "level": "LOW RISK",
                "description": "Manajemen Keuangan Baik"
            },
            "alert": {
                "type": "INFO",
                "message": f"""
✅ MANAJEMEN KEUANGAN BAIK ✅

Anda sedang melakukan manajemen keuangan dengan sangat baik!

Detail:
• Rasio Pengeluaran: {spending_ratio:.2f}%
• Total Tabungan: Rp {total_saving:,.2f}
• Total Pengeluaran: Rp {total_spending:,.2f}

Tetap pertahankan kinerja keuangan Anda!""",
                "recommendations": [
                    "Pertahankan pola pengeluaran saat ini",
                    "Lanjutkan kebiasaan menabung",
                    "Evaluasi berkala tetap diperlukan"
                ]
            },
            "risk_assessment": {
                "spending_risk_level": "LOW",
                "financial_health_index": 0.8  # High financial health
            }
        })

    return response

@app.route('/predict-spending/<string:user_id>/<string:month>', methods=['GET'])
def predict_spending(user_id, month):
    """Predict spending for a user in a specific month."""
    try:
        # Validate month format (YYYY-MM)
        try:
            datetime.strptime(month, '%Y-%m')
        except ValueError:
            return jsonify({"error": "Invalid month format. Use YYYY-MM"}), 400

        # Get user savings information
        savings_balance, savings_percentage, total_saving = get_user_savings_info(
            firestore_client, user_id, month
        )

        # Normalize the savings balance
        normalized_balance = np.clip(savings_balance, 0, 1e6) / 1e6

        # Retrieve transactions for the month
        transactions = get_transactions_for_month(firestore_client, user_id, month)

        if not transactions:
            return jsonify({"message": "No transactions found"}), 404

        # Aggregate transaction data
        total_spending = 0
        transaction_categories = []

        for transaction in transactions:
            transaction_data = transaction.to_dict()
            total_spending += transaction_data.get('amount', 0)
            transaction_categories.append(transaction_data.get('category', 'default'))

        # Determine the most frequent category
        most_frequent_category = max(set(transaction_categories), key=transaction_categories.count)

        user_id_encoded, category_encoded, amount_encoded = preprocess_input(user_id, most_frequent_category, total_spending)

        inputs = [
            np.array([[user_id_encoded]]),
            np.array([[category_encoded]]),
            np.array([[amount_encoded]])
        ]

        # Model prediction
        predicted_label = model.predict(inputs)[0][0]
        predicted_label = smooth_prediction(predicted_label)
        # Check if spending exceeds limits
        threshold = 0.7
        if total_spending > savings_balance:
            alert = "High Spending: Spending exceeds available savings."
        elif predicted_label > threshold:
            alert = check_spending(total_spending, savings_balance, savings_percentage)
        else:
            alert = "Spending is within limits."

        return jsonify({
            **generate_enhanced_spending_alert(
                total_spending=total_spending, 
                total_saving=total_saving,
                savings_balance=savings_balance, 
                savings_percentage=savings_percentage, 
                predicted_label=predicted_label
            ),
            "prediction": "High Spending" if total_spending > savings_balance or predicted_label > threshold else "Normal Spending"
        })


    except Exception as e:
        logging.error(f"Prediction error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
