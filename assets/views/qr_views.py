import qrcode
from PIL import Image, ImageDraw, ImageFont
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from assets.models import AssetUnit, UnitLog


def unit_qr_code(request, uuid):
    """Menghasilkan gambar PNG QR Code unik dengan label nama aset dan kode unit."""
    unit = get_object_or_404(AssetUnit, id_uuid=uuid)
    url = request.build_absolute_uri(f'/public/unit/{uuid}/')

    qr = qrcode.QRCode(version=1, box_size=12, border=2)
    qr.add_data(url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    text = f"{unit.asset.name} - {unit.unit_code}"

    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font = ImageFont.load_default()

    qr_w, qr_h = qr_img.size

    try:
        bbox = font.getbbox(text)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        text_w, text_h = font.getsize(text)

    padding = 20
    new_h = qr_h + text_h + padding * 2
    new_w = max(qr_w, text_w + padding * 2)

    img = Image.new('RGB', (new_w, new_h), color='white')
    img.paste(qr_img, ((new_w - qr_w) // 2, padding // 2))

    draw = ImageDraw.Draw(img)
    text_x = (new_w - text_w) // 2
    text_y = qr_h + (padding // 2) + 5
    draw.text((text_x, text_y), text, font=font, fill="black")

    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response


def unit_public_detail(request, uuid):
    """Halaman publik detail unit aset dan riwayat yang diakses saat memindai QR Code."""
    unit = get_object_or_404(AssetUnit, id_uuid=uuid)
    logs = UnitLog.objects.filter(unit=unit).order_by('-timestamp')

    return render(request, 'unit_public_detail.html', {
        'unit': unit,
        'logs': logs
    })
