```sql
DELIMITER //

CREATE PROCEDURE sp_ThanhToanVaXoaNo(
    IN p_MaBill VARCHAR(20), 
    IN p_SoTienNop DECIMAL(15,2)
)
BEGIN
    DECLARE v_ConThieu DECIMAL(15,2);
      
    -- Nếu có bất kỳ lỗi nào, hệ thống tự động Rollback (Hủy bỏ)[cite: 3]
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
    END;

    START TRANSACTION;

    -- 1. Lưu thông tin đóng tiền[cite: 3]
    INSERT INTO PhieuThu(MaBill, DaThu) VALUES (p_MaBill, p_SoTienNop);
      
    -- 2. Kiểm tra xem khách đã hết nợ chưa[cite: 3]
    SELECT ConThieu INTO v_ConThieu FROM PhieuThu 
    WHERE MaBill = p_MaBill ORDER BY SoPhieu DESC LIMIT 1;
      
    -- 3. Nếu hết nợ, cập nhật trạng thái "Đã thanh toán đủ" cho hóa đơn[cite: 3]
    IF v_ConThieu <= 0 THEN
        UPDATE HoaDon SET TrangThai = 'Đã thanh toán đủ' WHERE MaBill = p_MaBill;
    END IF;

    COMMIT;
END //

DELIMITER ;
```
