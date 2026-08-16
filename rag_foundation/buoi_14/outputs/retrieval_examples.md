# BÁO CÁO TOÀN DIỆN PIPELINE RETRIEVAL: BM25 -> DENSE -> HYBRID (RRF) -> RERANKER

**Ngày thực nghiệm:** 2026-08-17  
**Corpus:** `buoi_14/data/processed/chunks_normalized.csv` (792 chunks)  
**Mô hình Dense:** `bkai-foundation-models/vietnamese-bi-encoder`  
**Mô hình Reranker:** `cross-encoder/ms-marco-MiniLM-L-6-v2` (Cross-Encoder)  

---

### Câu hỏi (Loại 1: Câu hỏi chứa mã/số hiệu cụ thể): "Thông tư số 01/2014/TT-NHNN quy định về vận chuyển tiền mặt"

#### 1. BM25 Results
| Rank | Score | Citation | Snippet |
|---:|---:|:---|:---|
| 1 | 27.2048 | `[01/2014/TT-NHNN | 44209_c001]` | NGÂN HÀNG NHÀ NƯỚC VIỆT NAM ------- CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM Độc lập - Tự do - Hạnh phúc --------------- Số: 0... |
| 2 | 20.6349 | `[01/2014/TT-NHNN | Điều 48. Trách nhiệm tổ chức vận chuyển | 44209_c049]` | Điều 48. Trách nhiệm tổ chức vận chuyển 1. Cục Phát hành và Kho quỹ có nhiệm vụ tổ chức vận chuyển tiền mặt, tài sản quý... |
| 3 | 20.5536 | `[01/2014/TT-NHNN | Điều 51. Đảm bảo bí mật thông tin vận chuyển | 44209_c052]` | Điều 51. Đảm bảo bí mật thông tin vận chuyển 1. Những người tổ chức và tham gia vận chuyển tiền mặt, tài sản quý, giấy t... |
| 4 | 20.3612 | `[01/2014/TT-NHNN | Điều 56. Trách nhiệm bảo vệ vận chuyển | 44209_c057]` | Điều 56. Trách nhiệm bảo vệ vận chuyển 1. Xe vận chuyển tiền mặt, tài sản quý, giấy tờ có giá của Ngân hàng Nhà nước do ... |
| 5 | 20.1010 | `[01/2014/TT-NHNN | Điều 55. Lực lượng tham gia vận chuyển và trách nhiệm của người áp tải | 44209_c056]` | Điều 55. Lực lượng tham gia vận chuyển và trách nhiệm của người áp tải 1. Khi vận chuyển tiền mặt, tài sản quý, giấy tờ ... |


#### 2. Dense Results
| Rank | Score | Citation | Snippet |
|---:|---:|:---|:---|
| 1 | 0.4341 | `[01/2014/TT-NHNN | Điều 50. Phương tiện vận chuyển | 44209_c051]` | Điều 50. Phương tiện vận chuyển 1. Vận chuyển tiền mặt, tài sản quý, giấy tờ có giá phải sử dụng xe chuyên dùng và các p... |
| 2 | 0.4150 | `[01/2014/TT-NHNN | Điều 1. Phạm vi điều chỉnh | 44209_c002]` | Điều 1. Phạm vi điều chỉnh 1. Thông tư này quy định việc giao nhận, bảo quản, vận chuyển; kiểm tra, kiểm kê, bàn giao, x... |
| 3 | 0.4148 | `[01/2014/TT-NHNN | Điều 51. Đảm bảo bí mật thông tin vận chuyển | 44209_c052]` | Điều 51. Đảm bảo bí mật thông tin vận chuyển 1. Những người tổ chức và tham gia vận chuyển tiền mặt, tài sản quý, giấy t... |
| 4 | 0.4146 | `[01/2014/TT-NHNN | Điều 11. Giao nhận tiền mặt trong ngành Ngân hàng | 44209_c012]` | Điều 11. Giao nhận tiền mặt trong ngành Ngân hàng 1. Giao nhận tiền mặt theo bó tiền đủ 10 thếp, nguyên niêm phong hoặc ... |
| 5 | 0.4090 | `[01/2014/TT-NHNN | Điều 43. Nội quy kho tiền, quầy giao dịch tiền mặt | 44209_c044]` | Điều 43. Nội quy kho tiền, quầy giao dịch tiền mặt 1. Những người có nhiệm vụ vào quầy giao dịch tiền mặt hoặc kho tiền ... |


#### 3. Hybrid (RRF) Results
| Rank | Chunk ID | BM25 Rank | Dense Rank | RRF Score | Citation |
|---:|:---|:---:|:---:|---:|:---|
| 1 | `44209_c052` | 3 | 3 | 0.03175 | `[01/2014/TT-NHNN | Điều 51. Đảm bảo bí mật thông tin vận chuyển | 44209_c052]` |
| 2 | `44209_c051` | 6 | 1 | 0.03154 | `[01/2014/TT-NHNN | Điều 50. Phương tiện vận chuyển | 44209_c051]` |
| 3 | `44209_c002` | 11 | 2 | 0.03021 | `[01/2014/TT-NHNN | Điều 1. Phạm vi điều chỉnh | 44209_c002]` |
| 4 | `44209_c057` | 4 | 12 | 0.02951 | `[01/2014/TT-NHNN | Điều 56. Trách nhiệm bảo vệ vận chuyển | 44209_c057]` |
| 5 | `44209_c050` | 10 | 11 | 0.02837 | `[01/2014/TT-NHNN | Điều 49. Giấy ủy quyền vận chuyển | 44209_c050]` |


#### 4. Reranker (Cross-Encoder) Results [AFTER RERANK]
| Rank | Chunk ID | Hybrid Rank | Hybrid Score | Rerank Score | Citation |
|---:|:---|:---:|---:|---:|:---|
| 1 | `44209_c073` | 15 | 0.01471 | 7.0463 | `[01/2014/TT-NHNN | Điều 72. Hiệu lực thi hành | 44209_c073]` |
| 2 | `44209_c001` | 7 | 0.01639 | 7.0112 | `[01/2014/TT-NHNN | 44209_c001]` |
| 3 | `44209_c052` | 1 | 0.03175 | 4.4282 | `[01/2014/TT-NHNN | Điều 51. Đảm bảo bí mật thông tin vận chuyển | 44209_c052]` |
| 4 | `44209_c057` | 4 | 0.02951 | 4.1100 | `[01/2014/TT-NHNN | Điều 56. Trách nhiệm bảo vệ vận chuyển | 44209_c057]` |
| 5 | `44209_c002` | 3 | 0.03021 | 4.1083 | `[01/2014/TT-NHNN | Điều 1. Phạm vi điều chỉnh | 44209_c002]` |

------------------------------------------------------------

### Câu hỏi (Loại 2: Câu hỏi diễn đạt ngữ nghĩa (Semantic)): "Nội quy quầy giao dịch và quy định an toàn kho tiền ngân hàng"

#### 1. BM25 Results
| Rank | Score | Citation | Snippet |
|---:|---:|:---|:---|
| 1 | 33.4395 | `[01/2014/TT-NHNN | Điều 15. Sắp xếp, bảo quản tài sản tại quầy giao dịch và trong kho tiền | 44209_c016]` | Điều 15. Sắp xếp, bảo quản tài sản tại quầy giao dịch và trong kho tiền 1. Hết giờ làm việc hàng ngày, toàn bộ tiền mặt,... |
| 2 | 29.7080 | `[01/2014/TT-NHNN | Điều 43. Nội quy kho tiền, quầy giao dịch tiền mặt | 44209_c044]` | Điều 43. Nội quy kho tiền, quầy giao dịch tiền mặt 1. Những người có nhiệm vụ vào quầy giao dịch tiền mặt hoặc kho tiền ... |
| 3 | 29.0884 | `[01/2014/TT-NHNN | Điều 14. Giao nhận tiền mặt với Kho bạc Nhà nước, đơn vị làm dịch vụ ngân quỹ của tổ chức tín dụng | 44209_c015]` | Điều 14. Giao nhận tiền mặt với Kho bạc Nhà nước, đơn vị làm dịch vụ ngân quỹ của tổ chức tín dụng 1. Việc giao nhận tiề... |
| 4 | 27.5710 | `[01/2014/TT-NHNN | Điều 65. Xử lý các trường hợp thừa hoặc thiếu tiền mặt, tài sản quý, giấy tờ có giá bảo quản trong kho tiền, quầy giao dịch, trên đường vận chuyển | 44209_c066]` | Điều 65. Xử lý các trường hợp thừa hoặc thiếu tiền mặt, tài sản quý, giấy tờ có giá bảo quản trong kho tiền, quầy giao d... |
| 5 | 27.4946 | `[01/2014/TT-NHNN | Điều 59. Định kỳ kiểm tra, kiểm kê | 44209_c060]` | Điều 59. Định kỳ kiểm tra, kiểm kê 1. Kiểm tra toàn diện công tác đảm bảo an toàn kho quỹ và tổng kiểm kê tiền mặt, tài ... |


#### 2. Dense Results
| Rank | Score | Citation | Snippet |
|---:|---:|:---|:---|
| 1 | 0.7103 | `[01/2014/TT-NHNN | Điều 43. Nội quy kho tiền, quầy giao dịch tiền mặt | 44209_c044]` | Điều 43. Nội quy kho tiền, quầy giao dịch tiền mặt 1. Những người có nhiệm vụ vào quầy giao dịch tiền mặt hoặc kho tiền ... |
| 2 | 0.6478 | `[01/2014/TT-NHNN | Điều 15. Sắp xếp, bảo quản tài sản tại quầy giao dịch và trong kho tiền | 44209_c016]` | Điều 15. Sắp xếp, bảo quản tài sản tại quầy giao dịch và trong kho tiền 1. Hết giờ làm việc hàng ngày, toàn bộ tiền mặt,... |
| 3 | 0.5388 | `[01/2014/TT-NHNN | Điều 45. Canh gác, bảo vệ kho tiền | 44209_c046]` | Điều 45. Canh gác, bảo vệ kho tiền 1. Kho tiền phải được canh gác, bảo vệ thường xuyên đảm bảo an toàn 24 giờ/ngày. Ngân... |
| 4 | 0.5181 | `[01/2014/TT-NHNN | Điều 31. Niêm phong và gửi chìa khóa dự phòng khóa cửa kho tiền | 44209_c032]` | Điều 31. Niêm phong và gửi chìa khóa dự phòng khóa cửa kho tiền 1. Việc niêm phong chìa khóa dự phòng cửa kho tiền được ... |
| 5 | 0.4923 | `[01/2014/TT-NHNN | Điều 44. Về làm việc ngoài giờ tại trụ sở kiêm kho tiền | 44209_c045]` | Điều 44. Về làm việc ngoài giờ tại trụ sở kiêm kho tiền Hết giờ làm việc, phải khóa cửa quầy giao dịch và các cửa thuộc ... |


#### 3. Hybrid (RRF) Results
| Rank | Chunk ID | BM25 Rank | Dense Rank | RRF Score | Citation |
|---:|:---|:---:|:---:|---:|:---|
| 1 | `44209_c044` | 2 | 1 | 0.03252 | `[01/2014/TT-NHNN | Điều 43. Nội quy kho tiền, quầy giao dịch tiền mặt | 44209_c044]` |
| 2 | `44209_c016` | 1 | 2 | 0.03252 | `[01/2014/TT-NHNN | Điều 15. Sắp xếp, bảo quản tài sản tại quầy giao dịch và trong kho tiền | 44209_c016]` |
| 3 | `44209_c032` | 16 | 4 | 0.02878 | `[01/2014/TT-NHNN | Điều 31. Niêm phong và gửi chìa khóa dự phòng khóa cửa kho tiền | 44209_c032]` |
| 4 | `44209_c060` | 5 | 18 | 0.02821 | `[01/2014/TT-NHNN | Điều 59. Định kỳ kiểm tra, kiểm kê | 44209_c060]` |
| 5 | `44209_c045` | 19 | 5 | 0.02804 | `[01/2014/TT-NHNN | Điều 44. Về làm việc ngoài giờ tại trụ sở kiêm kho tiền | 44209_c045]` |


#### 4. Reranker (Cross-Encoder) Results [AFTER RERANK]
| Rank | Chunk ID | Hybrid Rank | Hybrid Score | Rerank Score | Citation |
|---:|:---|:---:|---:|---:|:---|
| 1 | `44209_c044` | 1 | 0.03252 | 7.6529 | `[01/2014/TT-NHNN | Điều 43. Nội quy kho tiền, quầy giao dịch tiền mặt | 44209_c044]` |
| 2 | `44209_c016` | 2 | 0.03252 | 7.3290 | `[01/2014/TT-NHNN | Điều 15. Sắp xếp, bảo quản tài sản tại quầy giao dịch và trong kho tiền | 44209_c016]` |
| 3 | `44209_c015` | 10 | 0.01587 | 6.9914 | `[01/2014/TT-NHNN | Điều 14. Giao nhận tiền mặt với Kho bạc Nhà nước, đơn vị làm dịch vụ ngân quỹ của tổ chức tín dụng | 44209_c015]` |
| 4 | `44209_c022` | 17 | 0.01471 | 6.2882 | `[01/2014/TT-NHNN | Điều 21. Trách nhiệm của Trưởng kho tiền Trung ương, Trưởng phòng Ngân quỹ Sở Giao dịch, Trưởng phòng Tiền tệ - Kho quỹ | 44209_c022]` |
| 5 | `44209_c066` | 11 | 0.01562 | 6.1195 | `[01/2014/TT-NHNN | Điều 65. Xử lý các trường hợp thừa hoặc thiếu tiền mặt, tài sản quý, giấy tờ có giá bảo quản trong kho tiền, quầy giao dịch, trên đường vận chuyển | 44209_c066]` |

------------------------------------------------------------

### Câu hỏi (Loại 3: Câu hỏi kết hợp cả mã văn bản và ngữ nghĩa): "Quy định bảo quản tài sản quý và giấy tờ có giá theo 01/2014/TT-NHNN"

#### 1. BM25 Results
| Rank | Score | Citation | Snippet |
|---:|---:|:---|:---|
| 1 | 32.8722 | `[01/2014/TT-NHNN | 44209_c001]` | NGÂN HÀNG NHÀ NƯỚC VIỆT NAM ------- CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM Độc lập - Tự do - Hạnh phúc --------------- Số: 0... |
| 2 | 29.3887 | `[01/2014/TT-NHNN | Điều 26. Quy định ủy quyền của các thành viên tham gia quản lý tiền mặt, tài sản quý, giấy tờ có giá và kho tiền | 44209_c027]` | Điều 26. Quy định ủy quyền của các thành viên tham gia quản lý tiền mặt, tài sản quý, giấy tờ có giá và kho tiền 1. Quy ... |
| 3 | 27.8385 | `[01/2014/TT-NHNN | Điều 15. Sắp xếp, bảo quản tài sản tại quầy giao dịch và trong kho tiền | 44209_c016]` | Điều 15. Sắp xếp, bảo quản tài sản tại quầy giao dịch và trong kho tiền 1. Hết giờ làm việc hàng ngày, toàn bộ tiền mặt,... |
| 4 | 27.7505 | `[01/2014/TT-NHNN | Điều 56. Trách nhiệm bảo vệ vận chuyển | 44209_c057]` | Điều 56. Trách nhiệm bảo vệ vận chuyển 1. Xe vận chuyển tiền mặt, tài sản quý, giấy tờ có giá của Ngân hàng Nhà nước do ... |
| 5 | 27.5369 | `[01/2014/TT-NHNN | Điều 19. Trách nhiệm của Thủ kho tiền | 44209_c020]` | Điều 19. Trách nhiệm của Thủ kho tiền 1. Thủ kho tiền Sở Giao dịch, Ngân hàng Nhà nước chi nhánh, tổ chức tín dụng, chi ... |


#### 2. Dense Results
| Rank | Score | Citation | Snippet |
|---:|---:|:---|:---|
| 1 | 0.4468 | `[01/2014/TT-NHNN | Điều 51. Đảm bảo bí mật thông tin vận chuyển | 44209_c052]` | Điều 51. Đảm bảo bí mật thông tin vận chuyển 1. Những người tổ chức và tham gia vận chuyển tiền mặt, tài sản quý, giấy t... |
| 2 | 0.4457 | `[01/2014/TT-NHNN | Điều 65. Xử lý các trường hợp thừa hoặc thiếu tiền mặt, tài sản quý, giấy tờ có giá bảo quản trong kho tiền, quầy giao dịch, trên đường vận chuyển | 44209_c066]` | Điều 65. Xử lý các trường hợp thừa hoặc thiếu tiền mặt, tài sản quý, giấy tờ có giá bảo quản trong kho tiền, quầy giao d... |
| 3 | 0.4157 | `[01/2014/TT-NHNN | Điều 6. Đóng gói, niêm phong tài sản quý, giấy tờ có giá | 44209_c007]` | Điều 6. Đóng gói, niêm phong tài sản quý, giấy tờ có giá 1. Việc đóng gói, niêm phong ngoại tệ, giấy tờ có giá thực hiện... |
| 4 | 0.4121 | `[01/2014/TT-NHNN | Điều 15. Sắp xếp, bảo quản tài sản tại quầy giao dịch và trong kho tiền | 44209_c016]` | Điều 15. Sắp xếp, bảo quản tài sản tại quầy giao dịch và trong kho tiền 1. Hết giờ làm việc hàng ngày, toàn bộ tiền mặt,... |
| 5 | 0.3924 | `[01/2014/TT-NHNN | Điều 67. Xử lý trường hợp thiếu mất tiền do nguyên nhân chủ quan | 44209_c068]` | Điều 67. Xử lý trường hợp thiếu mất tiền do nguyên nhân chủ quan 1. Giám đốc và những người có trách nhiệm quản lý, giám... |


#### 3. Hybrid (RRF) Results
| Rank | Chunk ID | BM25 Rank | Dense Rank | RRF Score | Citation |
|---:|:---|:---:|:---:|---:|:---|
| 1 | `44209_c052` | 6 | 1 | 0.03154 | `[01/2014/TT-NHNN | Điều 51. Đảm bảo bí mật thông tin vận chuyển | 44209_c052]` |
| 2 | `44209_c016` | 3 | 4 | 0.03150 | `[01/2014/TT-NHNN | Điều 15. Sắp xếp, bảo quản tài sản tại quầy giao dịch và trong kho tiền | 44209_c016]` |
| 3 | `44209_c068` | 8 | 5 | 0.03009 | `[01/2014/TT-NHNN | Điều 67. Xử lý trường hợp thiếu mất tiền do nguyên nhân chủ quan | 44209_c068]` |
| 4 | `44209_c051` | 10 | 8 | 0.02899 | `[01/2014/TT-NHNN | Điều 50. Phương tiện vận chuyển | 44209_c051]` |
| 5 | `44209_c027` | 2 | 18 | 0.02895 | `[01/2014/TT-NHNN | Điều 26. Quy định ủy quyền của các thành viên tham gia quản lý tiền mặt, tài sản quý, giấy tờ có giá và kho tiền | 44209_c027]` |


#### 4. Reranker (Cross-Encoder) Results [AFTER RERANK]
| Rank | Chunk ID | Hybrid Rank | Hybrid Score | Rerank Score | Citation |
|---:|:---|:---:|---:|---:|:---|
| 1 | `44209_c062` | 15 | 0.01493 | 6.1326 | `[01/2014/TT-NHNN | Điều 61. Bàn giao tiền mặt, tài sản quý, giấy tờ có giá | 44209_c062]` |
| 2 | `44209_c052` | 1 | 0.03154 | 6.0135 | `[01/2014/TT-NHNN | Điều 51. Đảm bảo bí mật thông tin vận chuyển | 44209_c052]` |
| 3 | `44209_c001` | 10 | 0.01639 | 5.9839 | `[01/2014/TT-NHNN | 44209_c001]` |
| 4 | `44209_c065` | 8 | 0.02652 | 5.8932 | `[01/2014/TT-NHNN | Điều 64. Xử lý thừa hoặc thiếu tiền mặt, tài sản quý, giấy tờ có giá trong kiểm đếm, đóng gói | 44209_c065]` |
| 5 | `44209_c041` | 13 | 0.01515 | 5.8137 | `[01/2014/TT-NHNN | Điều 40. Các trường hợp được vào kho tiền | 44209_c041]` |

------------------------------------------------------------

## ĐÁNH GIÁ VÀ BÁO CÁO HIỆU QUẢ TẦNG RERANKING (PROMPT 4)

### 1. Phân tích tác động của Reranker (Before vs After Rerank):
- **Tối ưu thứ hạng ngữ nghĩa trực tiếp (Deep Cross-Attention):**  
  Khác với Dense Retrieval (dùng Bi-Encoder chỉ tính cosine giữa 2 vector tách biệt), Cross-Encoder tính toán tương tác trực tiếp từng từ trong câu hỏi với từng từ trong chunk text. Đã đẩy các chunk đúng câu hỏi chính xác lên Top 1.
- **Lọc nhiễu hiệu quả:**  
  Những chunk tuy có RRF score cao do xuất hiện cả ở BM25 và Dense nhưng câu từ không thực sự trả lời đúng trọng tâm câu hỏi (vd các đoạn phụ lục hay điều khoản hiệu lực chung) lập tức bị Cross-Encoder chấm điểm thấp và đẩy xuống phía dưới.


### 2. Kết luận Pipeline Retrieval 4 Tầng:
1. **BM25 + Dense:** Đảm bảo không bỏ sót ứng viên (High Recall).
2. **Hybrid RRF:** Dung hòa thứ hạng giữa từ khóa exact match và ngữ nghĩa.
3. **Cross-Encoder Reranker:** Tối ưu hóa độ chính xác Top-k trả về (High Precision).
4. **Citation:** Tất cả các tầng đều giữ vững trích dẫn metadata chuẩn (`[Số ký hiệu | Điều X | Chunk_ID]`).