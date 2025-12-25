test TestVietnamese {
  functions [ExpRouter]
  args {
    user_message #"
        tôi muốn scan mẫu vật tên là "corosion" với kích thước 270x270, với 3 dạng xung là square với amp = 2.1, tần số 200Hz; gauss với amp = 3.88, tần số 1000hz; chirp với tần số 2.97, tần số f1 = 500Hz, f2 = 1500hz; lift-off lần lượt là 1mm, 2mm, 3mm. lưu ý khi đặt tên thì đầu tiên là tên mẫu vật
    "#

    conversation_history [
      {role: "user", content: "who are you"},
      {role: "assistant", content: "I am a NDT experiment assistant. How can I help you?"},
    ]
  }
}