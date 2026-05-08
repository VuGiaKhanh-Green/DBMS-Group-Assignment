```sql
DELIMITER //

-- 1. THÊM HỢP ĐỒNG MỚI 
CREATE PROCEDURE sp_ThemHopDong(
    IN p_MaHD VARCHAR(15), 
    IN p_CCCD CHAR(12), 
    IN p_HoTen VARCHAR(100),
    IN p_QueQuan VARCHAR(200),
    IN p_MaPhong VARCHAR(10), 
    IN p_ThoiHan INT, 
    IN p_TienCoc DECIMAL(15,2),
    IN p_GiaThue DECIMAL(15,2)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;   -- Trả lại lỗi cho client
    END;

    START TRANSACTION;

    -- 1. Kiểm tra và thêm/cập nhật khách hàng
    IF NOT EXISTS (SELECT 1 FROM KhachHang WHERE CCCD = p_CCCD) THEN
        INSERT INTO KhachHang (CCCD, HoTen, QueQuan) VALUES (p_CCCD, p_HoTen, p_QueQuan);
    ELSE
        UPDATE KhachHang SET HoTen = p_HoTen, QueQuan = p_QueQuan WHERE CCCD = p_CCCD;
    END IF;

    -- 2. Kiểm tra khách có hợp đồng đang hiệu lực không
    IF EXISTS (SELECT 1 FROM HopDong WHERE CCCD = p_CCCD AND TrangThai = 'Còn hiệu lực') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Khách đã có hợp đồng đang hiệu lực, không thể thêm mới';
    END IF;

    -- 3. Thêm hợp đồng
    INSERT INTO HopDong(MaHD, CCCD, MaPhong, ThoiHan, TienCoc, TrangThai)
    VALUES (p_MaHD, p_CCCD, p_MaPhong, p_ThoiHan, p_TienCoc, 'Còn hiệu lực');

    -- 4. Cập nhật trạng thái phòng
    UPDATE PhongTro SET TrangThai = 'Đang được thuê' WHERE MaPhong = p_MaPhong;

    -- 5. Ghi nhận giá thuê đầu tiên
    INSERT INTO GiaPhong (MaHD, GiaTien, NgayAp)
    VALUES (p_MaHD, p_GiaThue, CURDATE());

    COMMIT;
END //

-- 2. HỦY HỢP ĐỒNG (Giải phóng phòng trống ngay lập tức)[cite: 3]
CREATE OR REPLACE PROCEDURE sp_HuyHopDong(IN p_MaHD VARCHAR(15))
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Lấy thông tin
    SELECT MaPhong INTO @v_MaPhong FROM HopDong WHERE MaHD = p_MaHD;
    SELECT TrangThai INTO @v_TrangThai FROM HopDong WHERE MaHD = p_MaHD;

    IF @v_MaPhong IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Hợp đồng không tồn tại';
    END IF;
    IF @v_TrangThai != 'Còn hiệu lực' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Hợp đồng không còn hiệu lực để hủy';
    END IF;

    UPDATE HopDong SET TrangThai = 'Bị hủy bỏ' WHERE MaHD = p_MaHD;

    -- Giải phóng phòng nếu không còn hợp đồng hiệu lực khác
    IF NOT EXISTS (
        SELECT 1 FROM HopDong 
        WHERE MaPhong = @v_MaPhong 
          AND TrangThai = 'Còn hiệu lực'
          AND MaHD != p_MaHD
    ) THEN
        UPDATE PhongTro SET TrangThai = 'Còn trống' WHERE MaPhong = @v_MaPhong;
    END IF;

    COMMIT;
END //

-- 3. Hủy dịch vụ

CREATE OR REPLACE PROCEDURE sp_HuyDichVu(IN p_MaDK INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT MaHD, TrangThai INTO @v_MaHD, @v_TrangThai FROM DangKyDichVu WHERE MaDK = p_MaDK;
    IF @v_MaHD IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mã đăng ký không tồn tại';
    END IF;
    IF @v_TrangThai != 'Còn hiệu lực' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Dịch vụ này đã bị hủy trước đó';
    END IF;

    UPDATE DangKyDichVu SET TrangThai = 'Đã hủy' WHERE MaDK = p_MaDK;

    COMMIT;
END //
--- 4. ĐĂNG KÝ DỊCH VỤ
CREATE OR REPLACE PROCEDURE sp_DangKyDichVu(
    IN p_MaHD VARCHAR(15),
    IN p_MaDV VARCHAR(10),
    IN p_ThangBD DATE,
    IN p_ThangKT DATE,
    IN p_SoLuong INT,
    IN p_DonGia DECIMAL(15,2)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Kiểm tra hợp đồng
    IF NOT EXISTS (SELECT 1 FROM HopDong WHERE MaHD = p_MaHD AND TrangThai = 'Còn hiệu lực') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Hợp đồng không tồn tại hoặc không còn hiệu lực';
    END IF;

    -- Kiểm tra dịch vụ
    SELECT LoaiDV INTO @v_LoaiDV FROM DichVu WHERE MaDV = p_MaDV;
    IF @v_LoaiDV IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mã dịch vụ không tồn tại';
    END IF;
    IF @v_LoaiDV != 'Lựa chọn' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Chỉ được đăng ký dịch vụ tự chọn';
    END IF;

    INSERT INTO DangKyDichVu (MaHD, MaDV, ThangBD, ThangKT, SoLuong, DonGia, TrangThai)
    VALUES (p_MaHD, p_MaDV, p_ThangBD, p_ThangKT, p_SoLuong, p_DonGia, 'Còn hiệu lực');

    COMMIT;
END //
DELIMITER ;

```
