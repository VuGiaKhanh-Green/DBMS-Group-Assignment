```sql
-- 1. BẢNG KHÁCH HÀNG (Lưu thông tin định danh)
CREATE TABLE KhachHang
(
    CCCD CHAR(12) PRIMARY KEY,
    HoTen NVARCHAR(100) NOT NULL,
    QueQuan NVARCHAR(200),
    CONSTRAINT CHK_CCCD_Check CHECK (CCCD NOT LIKE '%[^0-9]%') -- Chỉ cho phép nhập số
) ENGINE=InnoDB;

-- 2. BẢNG SỐ ĐIỆN THOẠI CỦA KHÁCH HÀNG
CREATE TABLE SDT_KhachHang
(
    CCCD CHAR(12),
    SDT VARCHAR(15),
    PRIMARY KEY (CCCD, SDT),
    FOREIGN KEY (CCCD) REFERENCES KhachHang(CCCD) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 3. BẢNG PHÒNG TRỌ
CREATE TABLE PhongTro
(
    MaPhong VARCHAR(10) PRIMARY KEY,
    DienTich DECIMAL(5, 2) NOT NULL CHECK (DienTich > 0),
    TrangThai NVARCHAR(50) DEFAULT N'Còn trống' 
        CHECK (TrangThai IN (N'Đang được thuê', N'Còn trống'))
) ENGINE=InnoDB;

-- 4. BẢNG DỊCH VỤ
CREATE TABLE DichVu
(
    MaDV VARCHAR(10) PRIMARY KEY,
    LoaiDV NVARCHAR(50) NOT NULL 
        CHECK (LoaiDV IN (N'Bắt buộc', N'Lựa chọn')),
    TenDV NVARCHAR(100) NOT NULL,
    DonVi NVARCHAR(20)
) ENGINE=InnoDB;

-- 5. BẢNG HỢP ĐỒNG ( Khách - Phòng)
CREATE TABLE HopDong
(
    MaHD VARCHAR(15) PRIMARY KEY,
    CCCD CHAR(12) NOT NULL,
    MaPhong VARCHAR(10) NOT NULL,
    NgayKy DATE DEFAULT (CURRENT_DATE),
    ThoiHan INT CHECK (ThoiHan > 0), -- Số tháng thuê
    TienCoc DECIMAL(15, 2) DEFAULT 0 CHECK (TienCoc >= 0),
    TrangThai NVARCHAR(50) NOT NULL 
        CHECK (TrangThai IN (N'Còn hiệu lực', N'Hết hiệu lực', N'Bị hủy bỏ')),
    FOREIGN KEY (CCCD) REFERENCES KhachHang(CCCD) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (MaPhong) REFERENCES PhongTro(MaPhong) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 6. BẢNG GIÁ PHÒNG (Thực thể yếu của Hợp đồng )
CREATE TABLE GiaPhong
(
    LanDoi INT AUTO_INCREMENT,
    MaHD VARCHAR(15),
    GiaTien DECIMAL(15, 2) NOT NULL CHECK (GiaTien > 0),
    NgayAp DATE NOT NULL,
    PRIMARY KEY (MaHD, LanDoi),
    FOREIGN KEY (MaHD) REFERENCES HopDong(MaHD) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 7. BẢNG ĐĂNG KÝ DỊCH VỤ (Dịch vụ khách chọn trong hợp đồng)
CREATE TABLE DangKyDichVu
(
    MaDK INT AUTO_INCREMENT PRIMARY KEY,
    MaHD VARCHAR(15) NOT NULL,
    MaDV VARCHAR(10) NOT NULL,
    ThangBD DATE,
    ThangKT DATE,
    SoLuong INT DEFAULT 1 CHECK (SoLuong > 0),
    DonGia DECIMAL(15, 2) CHECK (DonGia >= 0),
    FOREIGN KEY (MaHD) REFERENCES HopDong(MaHD) ON DELETE CASCADE,
    FOREIGN KEY (MaDV) REFERENCES DichVu(MaDV) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 8. BẢNG HÓA ĐƠN
CREATE TABLE HoaDon
(
    MaBill VARCHAR(20) PRIMARY KEY,
    MaHD VARCHAR(15) NOT NULL,
    TongTien DECIMAL(15, 2) DEFAULT 0,
    NgayLap DATE DEFAULT (CURRENT_DATE),
    TrangThai NVARCHAR(50) DEFAULT N'Chưa thanh toán',
    KyHoaDon VARCHAR(10), -- Ví dụ: '04/2026'
    FOREIGN KEY (MaHD) REFERENCES HopDong(MaHD) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 9. BẢNG CHI TIẾT HÓA ĐƠN (Thành phần của Hóa đơn)
CREATE TABLE ChiTietHoaDon
(
    MaBill VARCHAR(20),
    Loai NVARCHAR(50) CHECK (Loai IN (N'TienPhong', N'TienDichVu')),
    MoTaChiTiet NVARCHAR(255),
    DonGia DECIMAL(15, 2) CHECK (DonGia >= 0),
    SoLuong INT CHECK (SoLuong >= 0),
    PRIMARY KEY (MaBill, Loai),
    FOREIGN KEY (MaBill) REFERENCES HoaDon(MaBill) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 10. BẢNG PHIẾU THU (Theo dõi các đợt trả tiền)
CREATE TABLE PhieuThu
(
    SoPhieu INT AUTO_INCREMENT PRIMARY KEY,
    MaBill VARCHAR(20) NOT NULL,
    DaThu DECIMAL(15, 2) DEFAULT 0 CHECK (DaThu >= 0),
    ConThieu DECIMAL(15, 2),
    NgayThu DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (MaBill) REFERENCES HoaDon(MaBill) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

```
