test TestVietnamese {
  functions [ExpRouter]
  args {
    user_message #"
        tôi muốn scan mẫu vật tên là "corosion" với kích thước 270x270, với 3 dạng xung là square với amp = 2.1, tần số 200Hz; gauss với amp = 3.88, tần số 1000hz; chirp với tần số 2.97, tần số f1 = 500Hz, f2 = 1500hz; lift-off lần lượt là 1mm, 2mm, 3mm. lưu ý khi đặt tên thì đầu tiên là tên mẫu vật
    "#
  }
}

test TestSimple {
  functions [ExpOrchestrator]
  args {
    reformatted_message "9 scans (3 waveforms x 3 lift-offs): square 270x270 amp=2.1 at 200Hz, gaussian 270x270 amp=3.88 at 1000Hz, chirp 270x270 amp=2.97 f1=500Hz f2=1500Hz, lift-offs [1mm, 2mm, 3mm], sample: corrosion, naming: sample name first"
  }
}