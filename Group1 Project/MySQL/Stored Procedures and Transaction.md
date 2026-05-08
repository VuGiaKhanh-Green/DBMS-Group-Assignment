```sql
DELIMITER //

-- =============================================
-- 1. THÊM HỢP ĐỒNG MỚI
-- =============================================
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
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Kiểm tra và thêm/cập nhật khách hàng
    IF NOT EXISTS (SELECT 1 FROM KhachHang WHERE CCCD = p_CCCD) THEN
        INSERT INTO KhachHang (CCCD, HoTen, QueQuan) VALUES (p_CCCD, p_HoTen, p_QueQuan);
    ELSE
        UPDATE KhachHang SET HoTen = p_HoTen, QueQuan = p_QueQuan WHERE CCCD = p_CCCD;
    END IF;

    -- Kiểm tra khách có hợp đồng đang hiệu lực không
    IF EXISTS (SELECT 1 FROM HopDong WHERE CCCD = p_CCCD AND TrangThai = 'Còn hiệu lực') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Khách đã có hợp đồng đang hiệu lực, không thể thêm mới';
    END IF;

    -- Thêm hợp đồng
    INSERT INTO HopDong(MaHD, CCCD, MaPhong, ThoiHan, TienCoc, TrangThai)
    VALUES (p_MaHD, p_CCCD, p_MaPhong, p_ThoiHan, p_TienCoc, 'Còn hiệu lực');

    -- Cập nhật trạng thái phòng
    UPDATE PhongTro SET TrangThai = 'Đang được thuê' WHERE MaPhong = p_MaPhong;

    -- Ghi nhận giá thuê đầu tiên
    INSERT INTO GiaPhong (MaHD, GiaTien, NgayAp)
    VALUES (p_MaHD, p_GiaThue, CURDATE());

    COMMIT;
END //

-- =============================================
-- 2. HỦY HỢP ĐỒNG
-- =============================================
CREATE PROCEDURE sp_HuyHopDong(IN p_MaHD VARCHAR(15))
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

-- =============================================
-- 3. ĐĂNG KÝ DỊCH VỤ (CHỈ DỊCH VỤ TỰ CHỌN)
-- =============================================
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

    -- Kiểm tra hợp đồng tồn tại và còn hiệu lực
    IF NOT EXISTS (SELECT 1 FROM HopDong WHERE MaHD = p_MaHD AND TrangThai = 'Còn hiệu lực') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Hợp đồng không tồn tại hoặc không còn hiệu lực';
    END IF;

    -- Kiểm tra dịch vụ có phải loại 'Lựa chọn'
    SELECT LoaiDV INTO @v_LoaiDV FROM DichVu WHERE MaDV = p_MaDV;
    IF @v_LoaiDV IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mã dịch vụ không tồn tại';
    END IF;
    IF @v_LoaiDV != 'Lựa chọn' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Chỉ được đăng ký dịch vụ tự chọn';
    END IF;

    -- Kiểm tra trùng lặp: đã có đăng ký còn hiệu lực cho cùng dịch vụ, cùng hợp đồng mà khoảng thời gian giao nhau?
    IF EXISTS (
        SELECT 1 FROM DangKyDichVu
        WHERE MaHD = p_MaHD
          AND MaDV = p_MaDV
          AND TrangThai = 'Còn hiệu lực'
          AND ThangBD <= p_ThangKT
          AND ThangKT >= p_ThangBD
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Dịch vụ này đã được đăng ký trong khoảng thời gian trùng lặp';
    END IF;

    -- Nếu không trùng, thêm mới
    INSERT INTO DangKyDichVu (MaHD, MaDV, ThangBD, ThangKT, SoLuong, DonGia, TrangThai)
    VALUES (p_MaHD, p_MaDV, p_ThangBD, p_ThangKT, p_SoLuong, p_DonGia, 'Còn hiệu lực');

    COMMIT;
END //


-- =============================================
-- 4. HỦY DỊCH VỤ
-- =============================================
CREATE PROCEDURE sp_HuyDichVu(IN p_MaDK INT)
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

-- =============================================
-- 5. TẠO HÓA ĐƠN (đã sửa lỗi, có transaction)
-- =============================================
CREATE PROCEDURE sp_TaoHoaDon(
    IN p_MaBill VARCHAR(20), 
    IN p_MaHD VARCHAR(15), 
    IN p_KyHoaDon VARCHAR(10)
)
BEGIN
    DECLARE v_TienPhong DECIMAL(15,2) DEFAULT 0;
    DECLARE v_TienDVBatBuoc DECIMAL(15,2) DEFAULT 0;
    DECLARE v_TienDVTuChon DECIMAL(15,2) DEFAULT 0;
    DECLARE v_TongTien DECIMAL(15,2) DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Kiểm tra hợp đồng còn hiệu lực
    IF NOT EXISTS (SELECT 1 FROM HopDong WHERE MaHD = p_MaHD AND TrangThai = 'Còn hiệu lực') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Hợp đồng không tồn tại hoặc không còn hiệu lực';
    END IF;

    -- Tiền phòng (giá mới nhất)
    SELECT GiaTien INTO v_TienPhong 
    FROM GiaPhong 
    WHERE MaHD = p_MaHD 
    ORDER BY NgayAp DESC 
    LIMIT 1;

    -- Tiền dịch vụ bắt buộc
    SELECT COALESCE(SUM(dk.SoLuong * dk.DonGia), 0) INTO v_TienDVBatBuoc
    FROM DangKyDichVu dk
    JOIN DichVu dv ON dk.MaDV = dv.MaDV
    WHERE dk.MaHD = p_MaHD 
      AND dv.LoaiDV = 'Bắt buộc'
      AND dk.TrangThai = 'Còn hiệu lực';

    -- Tiền dịch vụ tự chọn (còn hiệu lực và trong thời gian)
    SELECT COALESCE(SUM(dk.SoLuong * dk.DonGia), 0) INTO v_TienDVTuChon
    FROM DangKyDichVu dk
    JOIN DichVu dv ON dk.MaDV = dv.MaDV
    WHERE dk.MaHD = p_MaHD 
      AND dv.LoaiDV = 'Lựa chọn'
      AND dk.TrangThai = 'Còn hiệu lực'
      AND dk.ThangBD <= CURDATE() 
      AND dk.ThangKT >= CURDATE();

    SET v_TongTien = v_TienPhong + v_TienDVBatBuoc + v_TienDVTuChon;

    -- Thêm hóa đơn
    INSERT INTO HoaDon(MaBill, MaHD, TongTien, KyHoaDon, TrangThai)
    VALUES (p_MaBill, p_MaHD, v_TongTien, p_KyHoaDon, 'Còn thiếu');

    -- Thêm chi tiết hóa đơn: tiền phòng
    INSERT INTO ChiTietHoaDon (MaBill, Loai, MoTaChiTiet, DonGia, SoLuong)
    VALUES (p_MaBill, 'TienPhong', 'Tiền thuê phòng', v_TienPhong, 1);

    -- Nếu có tiền dịch vụ bắt buộc
    IF v_TienDVBatBuoc > 0 THEN
        INSERT INTO ChiTietHoaDon (MaBill, Loai, MoTaChiTiet, DonGia, SoLuong)
        VALUES (p_MaBill, 'TienDichVu', 'Dịch vụ bắt buộc', v_TienDVBatBuoc, 1);
    END IF;

    -- Nếu có tiền dịch vụ tự chọn
    IF v_TienDVTuChon > 0 THEN
        INSERT INTO ChiTietHoaDon (MaBill, Loai, MoTaChiTiet, DonGia, SoLuong)
        VALUES (p_MaBill, 'TienDichVu', 'Dịch vụ tự chọn', v_TienDVTuChon, 1);
    END IF;

    COMMIT;
END //

-- =============================================
-- 6. THANH TOÁN HÓA ĐƠN VÀ XÓA NỢ (giữ nguyên)
-- =============================================
CREATE PROCEDURE sp_ThanhToanVaXoaNo(
    IN p_MaBill VARCHAR(20), 
    IN p_SoTienNop DECIMAL(15,2)
)
BEGIN
    DECLARE v_ConThieu DECIMAL(15,2);
      
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- 1. Lưu phiếu thu
    INSERT INTO PhieuThu(MaBill, DaThu) VALUES (p_MaBill, p_SoTienNop);
      
    -- 2. Lấy số tiền còn thiếu mới nhất
    SELECT ConThieu INTO v_ConThieu FROM PhieuThu 
    WHERE MaBill = p_MaBill ORDER BY SoPhieu DESC LIMIT 1;
      
    -- 3. Nếu hết nợ, cập nhật trạng thái hóa đơn
    IF v_ConThieu <= 0 THEN
        UPDATE HoaDon SET TrangThai = 'Đã thanh toán đủ' WHERE MaBill = p_MaBill;
    END IF;

    COMMIT;
END //

DELIMITER ;
```
