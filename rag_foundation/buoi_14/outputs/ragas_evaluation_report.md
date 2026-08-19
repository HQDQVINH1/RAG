# BÁO CÁO ĐÁNH GIÁ HỆ THỐNG RAG VỚI RAGAS (BUỔI 14)

**Ngày thực thi:** 2026-08-19 20:45:48  
**Cấu hình Pipeline:**  
- **Retriever:** `SecureRetriever` (Hybrid Rerank: BM25 + Dense + Cross-Encoder)  
- **Generator LLM:** `Qwen/Qwen3.5-9B:deepinfra` (trỏ qua Hugging Face Router API, tắt reasoning)  
- **Judger LLM:** `openai/gpt-oss-20b:deepinfra` (`ChatOpenAI` qua HF Router API, tắt reasoning)  
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2`  
- **Tổng số câu hỏi đánh giá (Golden Dataset):** 20 câu  

---

## 1. TỔNG QUAN ĐIỂM SỐ TRUNG BÌNH (4 METRICS)

| Chỉ số Đánh giá (Metric) | Điểm Trung Bình | Ngưỡng Kỳ Vọng | Trạng Thái | Đánh Giá Chung |
| :--- | :---: | :---: | :---: | :--- |
| **Context Precision** | **0.8728** | $\ge 0.75$ | ✅ Đạt | Mức độ liên quan và sắp xếp thứ tự của các chunk truy xuất. |
| **Context Recall** | **0.9360** | $\ge 0.80$ | ✅ Đạt | Tỷ lệ ngữ cảnh truy xuất bao phủ đầy đủ đáp án chuẩn (ground truth). |
| **Faithfulness** | **1.0000** | $\ge 0.85$ | ✅ Đạt | Tính trung thực của câu trả lời, không tự phát sinh tri thức ảo. |
| **Answer Relevancy** | **0.8201** | $\ge 0.80$ | ✅ Đạt | Mức độ đi thẳng vào trọng tâm và đúng yêu cầu của câu hỏi. |
| **ĐIỂM TỔNG THỂ (OVERALL)** | **0.9073** | $\ge 0.80$ | ✅ Đạt | **Chỉ số đánh giá năng lực toàn diện của hệ thống RAG.** |

---

## 2. CHI TIẾT KẾT QUẢ ĐÁNH GIÁ TỪNG CÂU HỎI

| Mã CH | Nhóm Usecase | Độ Khó | Context Precision | Context Recall | Faithfulness | Answer Relevancy | Điểm Tổng Thể |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Q01** | HR | easy | 1.0000 | 1.0000 | 1.0000 | 0.6667 | **0.9167** |
| **Q02** | HR | easy | 0.5000 | 0.9289 | 1.0000 | 0.6000 | **0.7572** |
| **Q03** | HR | medium | 0.9000 | 1.0000 | 1.0000 | 0.8500 | **0.9375** |
| **Q04** | HR | easy | 0.9385 | 1.0000 | 1.0000 | 0.9615 | **0.9750** |
| **Q05** | HR | medium | 1.0000 | 1.0000 | 1.0000 | 0.7577 | **0.9394** |
| **Q06** | HR | hard | 0.5500 | 0.8800 | 1.0000 | 0.6853 | **0.7788** |
| **Q07** | HR | hard | 0.7885 | 0.7300 | 1.0000 | 0.8346 | **0.8383** |
| **Q08** | Risk | medium | 1.0000 | 1.0000 | 1.0000 | 0.8944 | **0.9736** |
| **Q09** | Risk | easy | 1.0000 | 1.0000 | 1.0000 | 0.9000 | **0.9750** |
| **Q10** | Risk | medium | 1.0000 | 1.0000 | 1.0000 | 0.5500 | **0.8875** |
| **Q11** | Risk | medium | 1.0000 | 1.0000 | 1.0000 | 0.9500 | **0.9875** |
| **Q12** | Risk | hard | 0.8214 | 0.8800 | 1.0000 | 1.0000 | **0.9254** |
| **Q13** | Risk | hard | 0.8500 | 0.8800 | 1.0000 | 1.0000 | **0.9325** |
| **Q14** | Risk | easy | 1.0000 | 0.7618 | 1.0000 | 1.0000 | **0.9405** |
| **Q15** | Common | easy | 0.9000 | 1.0000 | 1.0000 | 0.8333 | **0.9333** |
| **Q16** | Common | easy | 1.0000 | 1.0000 | 1.0000 | 1.0000 | **1.0000** |
| **Q17** | Common | medium | 1.0000 | 1.0000 | 1.0000 | 0.8944 | **0.9736** |
| **Q18** | Common | medium | 0.7750 | 0.9000 | 1.0000 | 0.8250 | **0.8750** |
| **Q19** | Common | hard | 0.8500 | 0.8800 | 1.0000 | 0.6500 | **0.8450** |
| **Q20** | Common | hard | 0.5833 | 0.8800 | 1.0000 | 0.5500 | **0.7533** |

---

## 3. PHÂN TÍCH NGUYÊN NHÂN LỖI ĐỐI VỚI CÁC CÂU HỎI ĐIỂM THẤP (< 0.70)

Tổng số câu hỏi có ít nhất một chỉ số $< 0.70$: **6 / 20 câu**.

### 🔴 Câu hỏi Q01 (HR - Độ khó: easy)
- **Nội dung câu hỏi:** *"Thời gian thử việc tối đa đối với chức danh quản lý doanh nghiệp theo quy định là bao nhiêu ngày?"*
- **Đáp án chuẩn (Ground Truth):** Thời gian thử việc tối đa đối với chức danh người quản lý doanh nghiệp theo quy định của Bộ luật Lao động là không quá 180 ngày.
- **Câu trả lời sinh ra:** Theo quy định tại văn bản: Điều 78. Tiêu chuẩn của Giám đốc hoặc Tổng giám đốc, người đại diện theo pháp luật
1. Các tiêu chuẩn chung quy định tại Điều 76 Nghị định này.
2. Có bằng đại học trở lên.
3. Có chứng chỉ bảo hiểm hoặc chứng chỉ môi giới bảo hiểm do các cơ sở đào tạo .
- **Điểm chi tiết:** Precision: `1.00`, Recall: `1.00`, Faithfulness: `1.00`, Relevancy: `0.67`
- **Nguyên nhân kỹ thuật chính:**
• **Lỗi Answer Relevancy thấp:** Câu trả lời còn dài dòng, chưa trả lời đúng trọng tâm câu hỏi.

### 🔴 Câu hỏi Q02 (HR - Độ khó: easy)
- **Nội dung câu hỏi:** *"Người lao động có được nghỉ làm việc và hưởng nguyên lương trong Ngày Quốc khánh không? Nghỉ bao nhiêu ngày?"*
- **Đáp án chuẩn (Ground Truth):** Người lao động được nghỉ làm việc và hưởng nguyên lương 02 ngày vào dịp Quốc khánh (ngày 02 tháng 9 dương lịch và 01 ngày liền kề trước hoặc sau).
- **Câu trả lời sinh ra:** Theo quy định tại văn bản: Điều 3. Số lượng nhân viên của Văn phòng đại diện
Số người nước ngoài (tới da): người;
Số người Việt Nam (tối thiểu): người..
- **Điểm chi tiết:** Precision: `0.50`, Recall: `0.93`, Faithfulness: `1.00`, Relevancy: `0.60`
- **Nguyên nhân kỹ thuật chính:**
• **Lỗi Context Precision thấp:** Các chunk nhiễu không liên quan xếp vị trí cao hơn chunk chứa thông tin cốt lõi.
• **Lỗi Answer Relevancy thấp:** Câu trả lời còn dài dòng, chưa trả lời đúng trọng tâm câu hỏi.

### 🔴 Câu hỏi Q06 (HR - Độ khó: hard)
- **Nội dung câu hỏi:** *"Mức tiền lương làm thêm giờ vào ngày nghỉ hằng tuần được tính tối thiểu bằng bao nhiêu phần trăm tiền lương giờ thực trả?"*
- **Đáp án chuẩn (Ground Truth):** Tiền lương làm thêm giờ vào ngày nghỉ hằng tuần được tính ít nhất bằng 200% tiền lương giờ thực trả của ngày làm việc bình thường.
- **Câu trả lời sinh ra:** Theo quy định tại văn bản: Điều 54. Tổ chức tiếp nhận
Khi tiền mặt, tài sản quý, giấy tờ có giá vận chuyển đến nơi nhận, đơn vị nhận hàng phải huy động lực lượng lao động trong đơn vị tiếp nhận hàng nhanh nhất (kể cả ngoài giờ làm việc hoặc ngày nghỉ) đưa hàng vào kho tiền bảo.
- **Điểm chi tiết:** Precision: `0.55`, Recall: `0.88`, Faithfulness: `1.00`, Relevancy: `0.69`
- **Nguyên nhân kỹ thuật chính:**
• **Lỗi Context Precision thấp:** Các chunk nhiễu không liên quan xếp vị trí cao hơn chunk chứa thông tin cốt lõi.
• **Lỗi Answer Relevancy thấp:** Câu trả lời còn dài dòng, chưa trả lời đúng trọng tâm câu hỏi.

### 🔴 Câu hỏi Q10 (Risk - Độ khó: medium)
- **Nội dung câu hỏi:** *"Khi phát hiện rủi ro vận hành có dấu hiệu gian lận nội bộ, đơn vị phải báo cáo Khối Quản trị Rủi ro trong thời hạn bao lâu?"*
- **Đáp án chuẩn (Ground Truth):** Đơn vị xảy ra sự cố phải gửi báo cáo nhanh ban đầu về Khối Quản trị Rủi ro trong vòng 24 giờ kể từ khi phát hiện sự việc.
- **Câu trả lời sinh ra:** Theo quy định tại văn bản: Điều 11. Giảm thiểu rủi ro tín dụng
1. Ngân hàng, chi nhánh ngân hàng nước ngoài được điều chỉnh giảm giá trị khoản phải đòi, giao dịch theo các biện pháp giảm thiểu rủi ro tín dụng quy định tại khoản 2 Điều này.
2. Việc giảm thiểu rủi ro tín dụng qu.
- **Điểm chi tiết:** Precision: `1.00`, Recall: `1.00`, Faithfulness: `1.00`, Relevancy: `0.55`
- **Nguyên nhân kỹ thuật chính:**
• **Lỗi Answer Relevancy thấp:** Câu trả lời còn dài dòng, chưa trả lời đúng trọng tâm câu hỏi.

### 🔴 Câu hỏi Q19 (Common - Độ khó: hard)
- **Nội dung câu hỏi:** *"Các loại tài khoản tiền gửi thanh toán của cá nhân bị đóng trong những trường hợp nào?"*
- **Đáp án chuẩn (Ground Truth):** Tài khoản thanh toán bị đóng khi có yêu cầu của chủ tài khoản, chủ tài khoản là cá nhân bị chết/mất tích, hoặc do tổ chức tín dụng chấm dứt theo thỏa thuận ban đầu.
- **Câu trả lời sinh ra:** Theo quy định tại văn bản: Điều 4. Nội dung hoạt động
Ngân hàng..... - Chi nhánh.... được thực hiện các hoạt động của loại hình ngân hàng thương mại theo quy định của pháp luật và của Ngân hàng Nhà nước Việt Nam, gồm các hoạt động sau đây:
1. Nhận tiền gửi không kỳ hạn, tiền g.
- **Điểm chi tiết:** Precision: `0.85`, Recall: `0.88`, Faithfulness: `1.00`, Relevancy: `0.65`
- **Nguyên nhân kỹ thuật chính:**
• **Lỗi Answer Relevancy thấp:** Câu trả lời còn dài dòng, chưa trả lời đúng trọng tâm câu hỏi.

### 🔴 Câu hỏi Q20 (Common - Độ khó: hard)
- **Nội dung câu hỏi:** *"Thời hạn lưu trữ hồ sơ tài liệu kế toán ngân hàng đối với chứng từ giao dịch trực tiếp tối thiểu là bao nhiêu năm?"*
- **Đáp án chuẩn (Ground Truth):** Chứng từ kế toán sử dụng trực tiếp để ghi sổ kế toán và lập báo cáo tài chính phải lưu trữ tối thiểu 10 năm theo quy định pháp luật kế toán.
- **Câu trả lời sinh ra:** Theo quy định tại văn bản: Điều 12. Chế độ lưu trữ tài liệu
1. Hợp tác xã, liên hiệp hợp tác xã phải lưu trữ theo quy định của pháp luật tài liệu sau:
a) Điều lệ và các quy chế của hợp tác xã, liên hiệp hợp tác xã; sổ đăng ký thành viên chính thức, thành viên liên kết góp vốn;.
- **Điểm chi tiết:** Precision: `0.58`, Recall: `0.88`, Faithfulness: `1.00`, Relevancy: `0.55`
- **Nguyên nhân kỹ thuật chính:**
• **Lỗi Context Precision thấp:** Các chunk nhiễu không liên quan xếp vị trí cao hơn chunk chứa thông tin cốt lõi.
• **Lỗi Answer Relevancy thấp:** Câu trả lời còn dài dòng, chưa trả lời đúng trọng tâm câu hỏi.

---

## 4. ĐỀ XUẤT TỐI ƯU HÓA HỆ THỐNG RAG

Dựa trên phân tích kết quả 4 chỉ số Ragas, hệ thống RAG cần được nâng cấp theo các giải pháp kỹ thuật sau:

1. **Cải thiện Context Recall (< 0.80):**
   - **Query Expansion:** Sử dụng LLM để mở rộng câu hỏi ban đầu bằng các từ đồng nghĩa pháp lý/ngân hàng trước khi đưa vào BM25 và Dense Search.
   - **Tăng Candidate List ($k$):** Nâng số lượng ứng viên truy xuất sơ bộ `candidate_k` từ 20 lên 40 trước khi chuyển qua Cross-Encoder Reranker.
   - **Graph Retrieval Synergy:** Tận dụng tri thức đồ thị Neo4j để lấy thêm các node lân cận (`DieuKhoan` $ightarrow$ `VanBan`).

2. **Cải thiện Context Precision (< 0.75):**
   - **Fine-tuning Reranker:** Tinh chỉnh mô hình Cross-Encoder (`BAAI/bge-reranker-v2-m3`) trên tập dữ liệu câu hỏi - điều khoản ngân hàng nội bộ.
   - **Điều chỉnh RRF Constant:** Thử nghiệm tham số $k$ trong công thức RRF (Reciprocal Rank Fusion) ở các mức $k=30, 60, 90$.

3. **Cải thiện Faithfulness & Answer Relevancy (< 0.85):**
   - **Strict System Prompting:** Siết chặt prompt hệ thống với quy tắc *"Chỉ trả lời chính xác thông tin có trong ngữ cảnh, tuyệt đối không suy đoán"*.
   - **Few-Shot Prompting:** Cung cấp 2-3 ví dụ mẫu về cấu trúc câu trả lời súc tích cho Generator.

---
*Báo cáo được khởi tạo tự động bởi `buoi_14/scripts/evaluate_rag_pipeline.py`.*
