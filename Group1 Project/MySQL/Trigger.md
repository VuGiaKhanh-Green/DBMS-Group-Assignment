```sql
DELIMITER //

CREATE TRIGGER trg_CapNhatDuNo
BEFORE INSERT ON PhieuThu
FOR EACH ROW
BEGIN
    DECLARE v_TongTien DECIMAL(15,2);
    DECLARE v_DaThuTruocDo DECIMAL(15,2);

    -- Lấy tổng tiền từ hóa đơn liên quan[cite: 3]
    SELECT TongTien INTO v_TongTien FROM HoaDon WHERE MaBill = NEW.MaBill;
    
    -- Tổng hợp số tiền khách đã đóng từ trước[cite: 3]
    SELECT COALESCE(SUM(DaThu), 0) INTO v_DaThuTruocDo 
    FROM PhieuThu WHERE MaBill = NEW.MaBill;

    -- Tự động tính nợ còn lại[cite: 3]
    SET NEW.ConThieu = v_TongTien - v_DaThuTruocDo - NEW.DaThu;
      
    IF NEW.ConThieu < 0 THEN
        SET NEW.ConThieu = 0;
    END IF;
END //

-- Trigger BEFORE UPDATE: nếu trạng thái "Còn hiệu lực" và đã hết hạn -> tự động đổi thành "Hết hiệu lực"
CREATE TRIGGER trg_HopDong_Update_HetHan
BEFORE UPDATE ON HopDong
FOR EACH ROW
BEGIN
    IF NEW.TrangThai = 'Còn hiệu lực' 
       AND DATE_ADD(NEW.NgayKy, INTERVAL NEW.ThoiHan MONTH) < CURDATE() 
    THEN
        SET NEW.TrangThai = 'Hết hiệu lực';
    END IF;
END //

-- Trigger BEFORE INSERT: phòng trường hợp insert hợp đồng đã hết hạn với trạng thái "Còn hiệu lực"
CREATE TRIGGER trg_HopDong_Insert_HetHan
BEFORE INSERT ON HopDong
FOR EACH ROW
BEGIN
    IF NEW.TrangThai = 'Còn hiệu lực' 
       AND DATE_ADD(NEW.NgayKy, INTERVAL NEW.ThoiHan MONTH) < CURDATE() 
    THEN
        SET NEW.TrangThai = 'Hết hiệu lực';
    END IF;
END //

DELIMITER ;
```
