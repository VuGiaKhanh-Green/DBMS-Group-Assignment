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
--- Set phòng còn trống khi hết hợp đồng---
CREATE TRIGGER trg_HopDong_Update_GiaiPhongPhong
AFTER UPDATE ON HopDong
FOR EACH ROW
BEGIN
    -- Chỉ xử lý nếu trạng thái thay đổi từ 'Còn hiệu lực' sang khác (Hết hiệu lực hoặc Bị hủy bỏ)
    IF OLD.TrangThai = 'Còn hiệu lực' AND NEW.TrangThai != 'Còn hiệu lực' THEN
        -- Kiểm tra xem phòng này còn hợp đồng nào 'Còn hiệu lực' khác không
        IF NOT EXISTS (
            SELECT 1 FROM HopDong 
            WHERE MaPhong = NEW.MaPhong 
              AND TrangThai = 'Còn hiệu lực'
              AND MaHD != NEW.MaHD
        ) THEN
            UPDATE PhongTro SET TrangThai = 'Còn trống' WHERE MaPhong = NEW.MaPhong;
        END IF;
    END IF;
END //

CREATE TRIGGER trg_DangKyDichVu_Update_HetHan
BEFORE UPDATE ON DangKyDichVu
FOR EACH ROW
BEGIN
    -- Nếu trạng thái là 'Còn hiệu lực' và ngày kết thúc đã qua -> tự chuyển sang 'Hết hiệu lực'
    IF NEW.TrangThai = 'Còn hiệu lực' AND NEW.ThangKT < CURDATE() THEN
        SET NEW.TrangThai = 'Hết hiệu lực';
    END IF;
END //

-- Tương tự cho INSERT (phòng trường hợp nhập dữ liệu cũ)
CREATE TRIGGER trg_DangKyDichVu_Insert_HetHan
BEFORE INSERT ON DangKyDichVu
FOR EACH ROW
BEGIN
    IF NEW.TrangThai = 'Còn hiệu lực' AND NEW.ThangKT < CURDATE() THEN
        SET NEW.TrangThai = 'Hết hiệu lực';
    END IF;
END //
DELIMITER ;
```
