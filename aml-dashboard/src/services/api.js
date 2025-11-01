// API Service for communicating with the FastAPI backend

const API_BASE_URL = 'http://localhost:4000';

/**
 * Upload a CSV file for transaction risk analysis
 * @param {File} file - CSV file containing transaction data
 * @returns {Promise<Object>} - API response with alerts and risk scores
 */
export const uploadTransactionCSV = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/infer_batch`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

/**
 * Transform API response to match transaction table format
 * @param {Object} apiResponse - Response from /api/v1/infer_batch
 * @returns {Array} - Transformed transaction data
 */
export const transformAPIResponse = (apiResponse) => {
  if (!apiResponse.alerts || apiResponse.alerts.length === 0) {
    return [];
  }

  return apiResponse.alerts.map((alert, index) => {
    // Risk_Score from API is 0-1 scale, convert to 0-100
    const riskScorePercent = Math.round((alert.Risk_Score || 0) * 100);

    return {
      id: `alert-${index}-${alert.Account_ID || ''}`,
      accountId: alert.Account_ID || 'Unknown',
      riskScore: riskScorePercent,
      riskRating: getRiskRating(alert.Risk_Score || 0),

      // Transaction volume (ensure numbers are valid)
      totalSent: parseFloat(alert.total_sent || 0).toFixed(2),
      numSentTx: parseInt(alert.num_sent_tx || 0),
      totalReceived: parseFloat(alert.total_received || 0).toFixed(2),
      numReceivedTx: parseInt(alert.num_received_tx || 0),

      // Averages
      avgSent: parseFloat(alert.avg_sent || 0).toFixed(2),
      avgReceived: parseFloat(alert.avg_received || 0).toFixed(2),

      // Risk patterns
      crossBorderSent: parseInt(alert.num_cross_border_tx_sent || 0),
      crossBorderReceived: parseInt(alert.num_cross_border_tx_received || 0),
      nightTxSent: parseInt(alert.num_night_tx_sent || 0),
      nightTxReceived: parseInt(alert.num_night_tx_received || 0),
      smallTxSent: parseInt(alert.num_small_tx_sent || 0),
      smallTxReceived: parseInt(alert.num_small_tx_received || 0),

      // Account behavior
      accountAgeDays: parseFloat(alert.account_age_days || 0).toFixed(1),
      txFrequencyPerDay: parseFloat(alert.tx_frequency_per_day || 0).toFixed(2),

      // Payment type features (optional, for detailed analysis)
      paymentFeatures: {
        sentCash: parseInt(alert.sent_feat_CASH || 0),
        sentIntlWire: parseInt(alert.sent_feat_INTL_WIRE || 0),
        sentDomesticFast: parseInt(alert.sent_feat_DOMESTIC_FAST || 0),
        sentLegacy: parseInt(alert.sent_feat_LEGACY || 0),
        receivedCash: parseInt(alert.received_feat_CASH || 0),
        receivedIntlWire: parseInt(alert.received_feat_INTL_WIRE || 0),
        receivedDomesticFast: parseInt(alert.received_feat_DOMESTIC_FAST || 0),
        receivedLegacy: parseInt(alert.received_feat_LEGACY || 0),
      }
    };
  });
};

/**
 * Determine risk rating based on risk score
 * @param {number} score - Risk score (0-1)
 * @returns {string} - Risk rating (High/Medium/Low)
 */
const getRiskRating = (score) => {
  if (score >= 0.85) return 'High';
  if (score >= 0.5) return 'Medium';
  return 'Low';
};
