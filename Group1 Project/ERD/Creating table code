

CREATE TABLE KhachHang (
    CCCD [Kiểu Dữ Liệu] PRIMARY KEY,
    HoTen [Kiểu Dữ Liệu],
    QueQuan [Kiểu Dữ Liệu]
);

CREATE TABLE PhongTro (
    MaPhong [Kiểu Dữ Liệu] PRIMARY KEY,
    DienTich [Kiểu Dữ Liệu],
    TrangThai [Kiểu Dữ Liệu]
);

CREATE TABLE DichVu (
    MaDV [Kiểu Dữ Liệu] PRIMARY KEY,
    LoaiDV [Kiểu Dữ Liệu],
    TenDV [Kiểu Dữ Liệu],
    DonVi [Kiểu Dữ Liệu]
);

CREATE TABLE SDT_KhachHang (
    CCCD [Kiểu Dữ Liệu],
    SDT [Kiểu Dữ Liệu],
    PRIMARY KEY (CCCD, SDT),
    FOREIGN KEY (CCCD) REFERENCES KhachHang(CCCD)
);

CREATE TABLE HopDong (
    MaHD [Kiểu Dữ Liệu] PRIMARY KEY,
    CCCD [Kiểu Dữ Liệu],
    MaPhong [Kiểu Dữ Liệu],
    ThoiHan [Kiểu Dữ Liệu],
    TrangThai [Kiểu Dữ Liệu],
    TienCoc [Kiểu Dữ Liệu],
    FOREIGN KEY (CCCD) REFERENCES KhachHang(CCCD),
    FOREIGN KEY (MaPhong) REFERENCES PhongTro(MaPhong)
);


CREATE TABLE GiaPhong (
    LanDoi [Kiểu Dữ Liệu],
    MaHD [Kiểu Dữ Liệu],
    GiaTien [Kiểu Dữ Liệu],
    NgayAp [Kiểu Dữ Liệu],
    PRIMARY KEY (LanDoi, MaHD),
    FOREIGN KEY (MaHD) REFERENCES HopDong(MaHD)
);

CREATE TABLE DangKyDichVu (
    MaDK [Kiểu Dữ Liệu] PRIMARY KEY,
    MaHD [Kiểu Dữ Liệu],
    MaDV [Kiểu Dữ Liệu],
    ThangBD [Kiểu Dữ Liệu],
    ThangKT [Kiểu Dữ Liệu],
    SoLuong [Kiểu Dữ Liệu],
    DonGia [Kiểu Dữ Liệu],
    FOREIGN KEY (MaHD) REFERENCES HopDong(MaHD),
    FOREIGN KEY (MaDV) REFERENCES DichVu(MaDV)
);

CREATE TABLE HoaDon (
    MaBill [Kiểu Dữ Liệu] PRIMARY KEY,
    MaHD [Kiểu Dữ Liệu],
    TongTien [Kiểu Dữ Liệu],
    NgayLap [Kiểu Dữ Liệu],
    TrangThai [Kiểu Dữ Liệu],
    KyHoaDon [Kiểu Dữ Liệu],
    FOREIGN KEY (MaHD) REFERENCES HopDong(MaHD)
);


CREATE TABLE ChiTietHoaDon (
    Loai [Kiểu Dữ Liệu],
    MaBill [Kiểu Dữ Liệu],
    DonGia [Kiểu Dữ Liệu],
    SoLuong [Kiểu Dữ Liệu],
    PRIMARY KEY (Loai, MaBill),
    FOREIGN KEY (MaBill) REFERENCES HoaDon(MaBill)
);

CREATE TABLE PhieuThu (
    SoPhieu [Kiểu Dữ Liệu] PRIMARY KEY,
    MaBill [Kiểu Dữ Liệu],
    DaThu [Kiểu Dữ Liệu],
    ConThieu [Kiểu Dữ Liệu],
    NgayThu [Kiểu Dữ Liệu],
    FOREIGN KEY (MaBill) REFERENCES HoaDon(MaBill)
);
