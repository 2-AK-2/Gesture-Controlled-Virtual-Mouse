import cv2  # type: ignore
import numpy as np  # type: ignore
import mediapipe as mp  # type: ignore
from scipy.spatial.distance import cosine  # type: ignore

class DanceMovementAnalyzer:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.reference_poses = []

    def extract_poses(self, video_path):
        cap = cv2.VideoCapture(video_path)
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break
            
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.pose.process(image_rgb)
            
            if results.pose_landmarks:
                pose_landmarks = np.array([[lm.x, lm.y, lm.z] for lm in results.pose_landmarks.landmark])
                self.reference_poses.append(pose_landmarks)
        
        cap.release()
        print(f"Extracted {len(self.reference_poses)} poses from the reference video.")

    def compare_pose(self, current_pose):
        if not self.reference_poses:
            return None, None

        min_distance = float('inf')
        best_match_index = -1

        for i, ref_pose in enumerate(self.reference_poses):
            distance = np.mean([cosine(current_pose[j], ref_pose[j]) for j in range(len(current_pose))])
            if distance < min_distance:
                min_distance = distance
                best_match_index = i

        similarity_score = 1 - min_distance
        return best_match_index, similarity_score

    def run_realtime_comparison(self):
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break

            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.pose.process(image_rgb)

            if results.pose_landmarks:
                current_pose = np.array([[lm.x, lm.y, lm.z] for lm in results.pose_landmarks.landmark])
                match_index, similarity_score = self.compare_pose(current_pose)

                if match_index is not None:
                    cv2.putText(image, f"Match: {match_index}, Similarity: {similarity_score:.2f}", 
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow('Dance Movement Comparison', image)
            if cv2.waitKey(5) & 0xFF == 27:  # Press 'Esc' to exit
                break

        cap.release()
        cv2.destroyAllWindows()

def main():
    analyzer = DanceMovementAnalyzer()
    
    print("Welcome to the Dance Movement Analysis and Comparison System!")
    reference_video = input("Please enter the path to your reference dance video: ")
    
    print("Analyzing reference video...")
    analyzer.extract_poses(reference_video)
    
    print("Analysis complete. Press 'Enter' to start real-time comparison, or 'q' to quit.")
    user_input = input()
    
    if user_input.lower() != 'q':
        print("Starting real-time comparison. Press 'Esc' to exit.")
        analyzer.run_realtime_comparison()
    
    print("Thank you for using the Dance Movement Analysis and Comparison System!")

if __name__ == "__main__":
    main()