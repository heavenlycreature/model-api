
# Spending Prediction API

This API predicts user spending behavior and provides financial insights, risk assessments, and recommendations. It is built with Flask, integrates with Firestore, and uses a TensorFlow model for predictions.

## Base URL
`http://<your-cloud-run-service-url>/`

## API Endpoints

### **Predict Spending**

Predicts user spending behavior and provides financial indicators, alerts, and risk assessments.

#### **URL**
`GET /predict-spending/<user_id>/<month>`

#### **Method**
`GET`

#### **Path Parameters**
| Parameter   | Type   | Description                                  | Example       |
|-------------|--------|----------------------------------------------|---------------|
| `user_id`   | string | Unique identifier for the user.              | `user123`     |
| `month`     | string | Month in `YYYY-MM` format.                   | `2024-12`     |

---

### **Responses**

#### **Success (200 OK)**
Returns spending prediction details, including financial indicators, alerts, and risk assessments.

**Example Response:**
```json
{
    "financial_indicators": {
        "total_spending": 500000,
        "savings_balance": 1000000,
        "savings_percentage": 20,
        "prediction_score": 0.75
    },
    "spending_status": {
        "code": "POTENTIAL_OVERSPENDING",
        "level": "MODERATE RISK",
        "description": "Pola Pengeluaran Berisiko"
    },
    "alert": {
        "type": "WARNING",
        "message": "⚠️ PERINGATAN POLA PENGELUARAN ⚠️

Pola pengeluaran Anda menunjukkan risiko keuangan.

Detail:
• Rasio Pengeluaran: 50.00%
• Total Tabungan: Rp 1,000,000.00
• Total Pengeluaran: Rp 500,000.00

Perhatian diperlukan untuk mencegah risiko keuangan!",
        "recommendations": [
            "Evaluasi pola pengeluaran",
            "Buat anggaran bulanan yang ketat",
            "Identifikasi area penghematan",
            "Pertimbangkan sumber pendapatan tambahan"
        ]
    },
    "risk_assessment": {
        "spending_risk_level": "MODERATE",
        "financial_health_index": 0.5
    },
    "prediction": "High Spending"
}
```

#### **Error Responses**
| Status Code | Message                                  | Description                                |
|-------------|------------------------------------------|--------------------------------------------|
| `400`       | `{"error": "Invalid month format. Use YYYY-MM"}` | Invalid `month` parameter format.           |
| `404`       | `{"message": "No transactions found"}`   | No transaction data found for the user.   |
| `500`       | `{"error": "<error-details>"}`           | Internal server error.                    |

---

### **Response Structure**

#### **Financial Indicators**
| Field              | Type   | Description                                    |
|--------------------|--------|------------------------------------------------|
| `total_spending`   | float  | Total spending by the user in the specified month. |
| `savings_balance`  | float  | User's total savings balance.                 |
| `savings_percentage` | float | Percentage of income saved.                   |
| `prediction_score` | float  | Spending risk prediction score (0.0 to 1.0).  |

#### **Spending Status**
| Field      | Type   | Description                                      |
|------------|--------|--------------------------------------------------|
| `code`     | string | Status code indicating the spending risk.        |
| `level`    | string | Risk level (`HIGH RISK`, `MODERATE RISK`, `LOW RISK`). |
| `description` | string | Description of the financial condition.       |

#### **Alert**
| Field             | Type        | Description                                    |
|-------------------|-------------|------------------------------------------------|
| `type`            | string      | Type of alert (`URGENT`, `WARNING`, `INFO`).   |
| `message`         | string      | Detailed message about the spending risk.      |
| `recommendations` | array       | List of recommendations for managing spending. |

#### **Risk Assessment**
| Field                  | Type   | Description                                    |
|------------------------|--------|------------------------------------------------|
| `spending_risk_level`  | string | Risk level (`HIGH`, `MODERATE`, `LOW`).        |
| `financial_health_index` | float  | A value representing the user's financial health (0.0 to 1.0). |

---

## Requirements

- Python 3.7+
- Flask
- TensorFlow
- Firestore
- Flask-CORS
- requests
- python-dotenv

---

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - `PORT`: Port for the app to listen on (e.g., `8080`).
   - `GOOGLE_APPLICATION_CREDENTIALS`: Path to your Firestore service account credentials.
   - `.env` file should contain the variables above.

4. Run the application:
   ```bash
   python app.py
   ```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
