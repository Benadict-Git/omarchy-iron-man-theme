"""Write ironman.script. Frame loading is spelled out line by line (no string
building at boot), and the password / progress logic is Omarchy's own, so the
disk-unlock flow behaves exactly as before -- only the visuals change."""
import sys
BOOT, IDLE = 24, 32
out = sys.argv[1]

load = "\n".join('boot_img[%d] = Image("boot-%02d.png");' % (i, i) for i in range(BOOT)) + "\n" + \
       "\n".join('idle_img[%d] = Image("idle-%02d.png");' % (i, i) for i in range(IDLE))

script = r'''# Iron Man Plymouth theme -- arc reactor unlock screen.
# Password and progress handling follow Omarchy's omarchy.script unchanged.

Window.SetBackgroundTopColor(0.027, 0.031, 0.043);
Window.SetBackgroundBottomColor(0.012, 0.012, 0.018);

#----------------------------------------- Arc reactor --------------------------------
boot_img = [];
idle_img = [];
%(load)s
global.boot_count = %(boot)d;
global.idle_count = %(idle)d;

logo.image = idle_img[0];
logo.sprite = Sprite(boot_img[0]);
logo.sprite.SetX(Window.GetWidth() / 2 - logo.image.GetWidth() / 2);
logo.sprite.SetY(Window.GetHeight() / 2 - logo.image.GetHeight() / 2 - 60);
logo.sprite.SetOpacity(1);

caption.ask = Image("caption-ask.png");
caption.boot = Image("caption-boot.png");
caption.sprite = Sprite(caption.ask);
caption.sprite.SetOpacity(0);

global.reactor_tick = 0;
global.reactor_speed = 1;

fun update_reactor() {
  global.reactor_tick = global.reactor_tick + global.reactor_speed;
  t = Math.Int(global.reactor_tick / 2);
  if (t < global.boot_count) {
    logo.sprite.SetImage(boot_img[t]);
  } else {
    i = t - global.boot_count;
    i = i - Math.Int(i / global.idle_count) * global.idle_count;
    logo.sprite.SetImage(idle_img[i]);
  }
}

fun show_caption(img) {
  caption.sprite.SetImage(img);
  caption.sprite.SetX(Window.GetWidth() / 2 - img.GetWidth() / 2);
  caption.sprite.SetY(logo.sprite.GetY() + logo.image.GetHeight() + 6);
  caption.sprite.SetOpacity(1);
}

# Use these to adjust the progress bar timing
global.fake_progress_limit = 0.7;
global.fake_progress_duration = 15.0;

global.animation_frame = 0;
global.fake_progress = 0.0;
global.real_progress = 0.0;
global.fake_progress_active = 0;
global.fake_progress_start_time = 0.0;
global.password_shown = 0;
global.max_progress = 0.0;

fun refresh_callback() {
  global.animation_frame++;
  update_reactor();

  if (global.fake_progress_active == 1) {
    elapsed_time = global.animation_frame / 50.0;
    time_ratio = elapsed_time / global.fake_progress_duration;
    if (time_ratio > 1.0) time_ratio = 1.0;
    eased_ratio = 1 - ((1 - time_ratio) * (1 - time_ratio));
    global.fake_progress = eased_ratio * global.fake_progress_limit;
    update_progress_bar(global.fake_progress);
  }
}

Plymouth.SetRefreshFunction(refresh_callback);

#----------------------------------------- Helper Functions --------------------------------

fun update_progress_bar(progress) {
  if (progress > global.max_progress) {
    global.max_progress = progress;
    width = Math.Int(progress_bar.original_image.GetWidth() * progress);
    if (width < 1) width = 1;
    progress_bar.image = progress_bar.original_image.Scale(width, progress_bar.original_image.GetHeight());
    progress_bar.sprite.SetImage(progress_bar.image);
  }
}

fun show_progress_bar() {
  progress_box.sprite.SetOpacity(1);
  progress_bar.sprite.SetOpacity(1);
}

fun hide_progress_bar() {
  progress_box.sprite.SetOpacity(0);
  progress_bar.sprite.SetOpacity(0);
}

fun show_password_dialog() {
  lock.sprite.SetOpacity(1);
  entry.sprite.SetOpacity(1);
}

fun hide_password_dialog() {
  lock.sprite.SetOpacity(0);
  entry.sprite.SetOpacity(0);
  for (index = 0; bullet.sprites[index]; index++) {
    bullet.sprites[index].SetOpacity(0);
  }
}

fun start_fake_progress() {
  global.fake_progress_active = 1;
  global.animation_frame = 0;
  global.max_progress = 0.0;
  global.fake_progress = 0.0;
  global.fake_progress_start_time = 0.0;
}

fun stop_fake_progress() {
  global.fake_progress_active = 0;
}

#----------------------------------------- Dialogue --------------------------------

lock.image = Image("lock.png");
entry.image = Image("entry.png");
bullet.image = Image("bullet.png");

entry.sprite = Sprite(entry.image);
entry.x = Window.GetWidth() / 2 - entry.image.GetWidth() / 2;
entry.y = logo.sprite.GetY() + logo.image.GetHeight() + 44;
entry.sprite.SetPosition(entry.x, entry.y, 10001);
entry.sprite.SetOpacity(0);

lock_height = entry.image.GetHeight() * 0.8;
lock_scale = lock_height / 96;
lock_width = 96 * lock_scale;

scaled_lock = lock.image.Scale(lock_width, lock_height);
lock.sprite = Sprite(scaled_lock);
lock.x = entry.x - lock_width - 15;
lock.y = entry.y + entry.image.GetHeight() / 2 - lock_height / 2;
lock.sprite.SetPosition(lock.x, lock.y, 10001);
lock.sprite.SetOpacity(0);

bullet.sprites = [];

fun display_normal_callback() {
  hide_password_dialog();
  mode = Plymouth.GetMode();
  if ((mode == "boot" || mode == "resume") && global.password_shown == 1) {
    show_caption(caption.boot);
    global.reactor_speed = 3;
    show_progress_bar();
    start_fake_progress();
  }
}

fun display_password_callback(prompt, bullets) {
  global.password_shown = 1;
  stop_fake_progress();
  hide_progress_bar();
  show_password_dialog();
  show_caption(caption.ask);
  global.reactor_speed = 1;

  for (index = 0; bullet.sprites[index]; index++) {
    bullet.sprites[index].SetOpacity(0);
  }

  max_bullets = 21;
  bullets_to_show = bullets;
  if (bullets_to_show > max_bullets) {
    bullets_to_show = max_bullets;
  }

  for (index = 0; index < bullets_to_show; index++) {
    if (!bullet.sprites[index]) {
      scaled_bullet = bullet.image.Scale(12, 12);
      bullet.sprites[index] = Sprite(scaled_bullet);
      bullet.x = entry.x + 22 + index * (12 + 6);
      bullet.y = entry.y + entry.image.GetHeight() / 2 - 6;
      bullet.sprites[index].SetPosition(bullet.x, bullet.y, 10002);
    }
    bullet.sprites[index].SetOpacity(1);
  }
}

Plymouth.SetDisplayNormalFunction(display_normal_callback);
Plymouth.SetDisplayPasswordFunction(display_password_callback);

#----------------------------------------- Progress Bar --------------------------------

progress_box.image = Image("progress_box.png");
progress_box.sprite = Sprite(progress_box.image);

progress_box.x = Window.GetWidth() / 2 - progress_box.image.GetWidth() / 2;
progress_box.y = entry.y + entry.image.GetHeight() / 2 - progress_box.image.GetHeight() / 2;
progress_box.sprite.SetPosition(progress_box.x, progress_box.y, 0);
progress_box.sprite.SetOpacity(0);

progress_bar.original_image = Image("progress_bar.png");
progress_bar.sprite = Sprite();
progress_bar.image = progress_bar.original_image.Scale(1, progress_bar.original_image.GetHeight());

progress_bar.x = Window.GetWidth() / 2 - progress_bar.original_image.GetWidth() / 2;
progress_bar.y = progress_box.y + (progress_box.image.GetHeight() - progress_bar.original_image.GetHeight()) / 2;
progress_bar.sprite.SetPosition(progress_bar.x, progress_bar.y, 1);
progress_bar.sprite.SetOpacity(0);

fun progress_callback(duration, progress) {
  if (global.fake_progress_start_time == 0.0) {
    global.fake_progress_start_time = duration;
  }
  global.real_progress = progress;
  if (duration > global.fake_progress_start_time && progress > global.fake_progress) {
    stop_fake_progress();
    update_progress_bar(progress);
  }
}

Plymouth.SetBootProgressFunction(progress_callback);

#----------------------------------------- Message --------------------------------

message_sprite = Sprite();
message_sprite.SetPosition(10, 10, 10000);

fun display_message_callback(text) {
  message = Image.Text(text, 1, 1, 1);
  message_sprite.SetImage(message);
  message_sprite.SetOpacity(1);
}

fun hide_message_callback(text) {
  message_sprite.SetOpacity(0);
}

Plymouth.SetDisplayMessageFunction(display_message_callback);
Plymouth.SetHideMessageFunction(hide_message_callback);
''' % dict(load=load, boot=BOOT, idle=IDLE)
open(out, "w").write(script)
print("wrote", out)
