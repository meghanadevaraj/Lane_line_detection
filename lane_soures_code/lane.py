import cv2
import numpy as np

# Open video file
vidcap = cv2.VideoCapture("lane_video3.mp4")
success, image = vidcap.read()

# Function to handle trackbar events
def nothing(x):
    pass

# Create trackbars for HSV thresholding
cv2.namedWindow("Trackbars")
cv2.createTrackbar("LH", "Trackbars", 0, 255, nothing)
cv2.createTrackbar("LS", "Trackbars", 0, 255, nothing)
cv2.createTrackbar("LV", "Trackbars", 200, 255, nothing)
cv2.createTrackbar("UH", "Trackbars", 255, 255, nothing)
cv2.createTrackbar("US", "Trackbars", 50, 255, nothing)
cv2.createTrackbar("UV", "Trackbars", 255, 255, nothing)

while success:
    success, image = vidcap.read()  # Read frame
    if not success:
        break

    frame = cv2.resize(image, (640, 480))

    # Choosing points for perspective transformation
    tl = (222, 387)
    bl = (70, 472)
    tr = (400, 380)
    br = (538, 472)

    # Draw circles for the points
    cv2.circle(frame, tl, 5, (0, 0, 255), -1)
    cv2.circle(frame, bl, 5, (0, 0, 255), -1)
    cv2.circle(frame, tr, 5, (0, 0, 255), -1)
    cv2.circle(frame, br, 5, (0, 0, 255), -1)

    # Applying perspective transformation
    pts1 = np.float32([tl, bl, tr, br])
    pts2 = np.float32([[0, 0], [0, 480], [640, 0], [640, 480]])

    # Matrix to warp the image for bird's-eye view
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    transformed_frame = cv2.warpPerspective(frame, matrix, (640, 480))

    # Image Thresholding
    hsv_transformed_frame = cv2.cvtColor(transformed_frame, cv2.COLOR_BGR2HSV)

    # Get trackbar positions
    l_h = cv2.getTrackbarPos("LH", "Trackbars")
    l_s = cv2.getTrackbarPos("LS", "Trackbars")
    l_v = cv2.getTrackbarPos("LV", "Trackbars")
    u_h = cv2.getTrackbarPos("UH", "Trackbars")
    u_s = cv2.getTrackbarPos("US", "Trackbars")
    u_v = cv2.getTrackbarPos("UV", "Trackbars")

    # Define the range for masking
    lower = np.array([l_h, l_s, l_v])
    upper = np.array([u_h, u_s, u_v])

    # Create the mask
    mask = cv2.inRange(hsv_transformed_frame, lower, upper)

    # Histogram
    histogram = np.sum(mask[mask.shape[0] // 2:, :], axis=0)
    midpoint = int(histogram.shape[0] / 2)

    left_base = np.argmax(histogram[:midpoint])
    right_base = np.argmax(histogram[midpoint:]) + midpoint

    # Sliding window
    y = 472
    lx = []
    rx = []
    msk = mask.copy()

    while y > 0:
        # Left threshold
        img_left = mask[y-48:y, left_base-50:left_base+50]
        contours, _ = cv2.findContours(img_left, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                lx.append(left_base - 50 + cx)
                left_base = left_base - 50 + cx

        # Right threshold
        img_right = mask[y-48:y, right_base-50:right_base+50]
        contours, _ = cv2.findContours(img_right, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                rx.append(right_base - 50 + cx)
                right_base = right_base - 50 + cx

        # Draw rectangles around detected windows
        cv2.rectangle(msk, (left_base-50, y), (left_base+50, y-40), (255, 255, 255), 2)
        cv2.rectangle(msk, (right_base-50, y), (right_base+50, y-40), (255, 255, 255), 2)

        y -= 40

    # Display images
    cv2.imshow("Original", frame)
    cv2.imshow("Bird's Eye View", transformed_frame)
    cv2.imshow("Lane Detection Image Thresholding", mask)
    cv2.imshow("Lane Detection Sliding Windows", msk)

    # Exit on pressing 'Esc'
    if cv2.waitKey(40) == 27:
        break

# Release video capture and close windows
vidcap.release()
cv2.destroyAllWindows()
