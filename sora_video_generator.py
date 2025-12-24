"""
Sora Video Generator

A class to handle video generation using the Sora 2 Proxy API.
Supports creating videos, checking pending tasks, and polling for completion.
"""

import time
import requests
from typing import Optional, Dict, Any, List

class SoraVideoGenerator:
    """Class to handle video generation via Sora 2 Proxy API"""
    
    def __init__(self):
        """
        Initialize the Sora Video Generator client.
        
        Args:
            api_base_url: Base URL for the Sora 2 Proxy API (default: from env or http://localhost:8000)
            api_key: API key for authentication (optional, from env if not provided)
            default_profile_id: Default AdsPower profile ID to use (optional)
        """
        self.api_base_url = "http://34.57.2.31"

        self.api_base_url = self.api_base_url.rstrip('/')
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
        }

        return headers
    
    def create_video(
        self,
        prompt: str,
        title: Optional[str] = None,
        orientation: str = "portrait",
        size: str = "small",
        n_frames: int = 300,
        model: str = "sy_8",
        style_id: Optional[str] = None,
        audio_caption: Optional[str] = None,
        audio_transcript: Optional[str] = None,
        video_caption: Optional[str] = None,
        storyboard_id: Optional[str] = None,
        remix_target_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new video generation task.
        
        Args:
            prompt: Video generation prompt (required)
            title: Video title (optional)
            orientation: "portrait", "landscape", or "square" (default: "portrait")
            size: "small", "medium", or "large" (default: "small")
            n_frames: Number of frames (default: 300)
            model: Model to use (default: "sy_8")
            style_id: Style ID (optional)
            audio_caption: Audio caption (optional)
            audio_transcript: Audio transcript (optional)
            video_caption: Video caption (optional)
            storyboard_id: Storyboard ID (optional)
            remix_target_id: Remix target ID (optional)
            **kwargs: Additional parameters
        
        Returns:
            Dictionary containing task ID and other metadata:
            {
                "id": "task_id",
                "priority": int,
                "rate_limit_and_credit_balance": dict,
                "profile_id": str
            }
        
        Raises:
            requests.HTTPError: If the API request fails
            ValueError: If required parameters are missing
        """
        if not prompt:
            raise ValueError("prompt is required")
        
        url = f"{self.api_base_url}/api/v1/create"
        
        payload = {
            "prompt": prompt,
            "kind": "video",
            "orientation": orientation,
            "size": size,
            "n_frames": n_frames,
            "model": model,
        }
        
        # Add optional parameters
        if title:
            payload["title"] = title
        if style_id:
            payload["style_id"] = style_id
        if audio_caption:
            payload["audio_caption"] = audio_caption
        if audio_transcript:
            payload["audio_transcript"] = audio_transcript
        if video_caption:
            payload["video_caption"] = video_caption
        if storyboard_id:
            payload["storyboard_id"] = storyboard_id
        if remix_target_id:
            payload["remix_target_id"] = remix_target_id
        
        # Add any additional kwargs
        payload.update(kwargs)
        
        response = requests.post(url, json=payload, headers=self._get_headers())
        response.raise_for_status()
        
        return response.json()
    
    def get_pending_tasks(self, profile_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all pending tasks for a specific profile.
        
        Args:
            profile_id: AdsPower profile ID (required if not set as default)
        
        Returns:
            Dictionary containing:
            {
                "profile_id": str,
                "pending_tasks": List[Dict],
                "count": int
            }
        
        Raises:
            requests.HTTPError: If the API request fails
            ValueError: If profile_id is not provided
        """
        if not profile_id:
            raise ValueError("profile_id is required (set as default or pass as parameter)")
        
        url = f"{self.api_base_url}/api/v1/tasks/pending"
        params = {"profile_id": profile_id}
        
        response = requests.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()
        
        return response.json()
    
    def get_task_status(
        self,
        task_id: str,
        profile_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the status of a video generation task.
        
        Args:
            task_id: The task ID returned from create_video
            profile_id: AdsPower profile ID (required if not set as default)
        
        Returns:
            List of task status dictionaries (usually one task):
            [{
                "id": str,
                "status": str,  # "queued", "processing", "completed", "failed"
                "prompt": str,
                "title": str,
                "progress_pct": float,
                "generations": List[Dict]
            }]
        
        Raises:
            requests.HTTPError: If the API request fails
            ValueError: If profile_id is not provided
        """
        if not profile_id:
            raise ValueError("profile_id is required (set as default or pass as parameter)")
        
        url = f"{self.api_base_url}/api/v1/task/{task_id}/status"
        params = {"profile_id": profile_id}
        
        response = requests.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()
        
        return response.json()
    
    def is_task_pending(
        self,
        task_id: str,
        profile_id: Optional[str] = None
    ) -> bool:
        """
        Check if a task is still pending (queued or processing).
        
        Args:
            task_id: The task ID to check
            profile_id: AdsPower profile ID (required if not set as default)
        
        Returns:
            True if task is pending, False otherwise
        
        Raises:
            requests.HTTPError: If the API request fails
        """
        try:
            # First check pending tasks list
            pending_tasks_data = self.get_pending_tasks(profile_id)
            pending_tasks = pending_tasks_data.get("pending_tasks", [])
            
            for task in pending_tasks:
                if task.get("id") == task_id:
                    status = task.get("status", "").lower()
                    return status in ["queued", "processing", "pending"]
            
            # If not in pending list, check status endpoint
            status_list = self.get_task_status(task_id, profile_id)
            if status_list:
                status = status_list[0].get("status", "").lower()
                return status in ["queued", "processing", "pending"]
            
            return False
        except Exception as e:
            # If we can't determine, assume not pending
            print(f"Error checking task status: {e}")
            return False
    
    def poll_task_until_complete(
        self,
        task_id: str,
        profile_id: Optional[str] = None,
        poll_interval: int = 60,
        max_wait: int = 1200,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Poll a task until it completes or times out.
        
        This method checks pending tasks and task status until the task is completed.
        Similar to the polling logic provided in the API server code.
        
        Args:
            task_id: The task ID to poll
            profile_id: AdsPower profile ID (required if not set as default)
            poll_interval: Seconds between status checks (default: 60)
            max_wait: Maximum seconds to wait (default: 1200 = 20 minutes)
            verbose: Whether to print progress messages (default: True)
        
        Returns:
            Dictionary containing completed video draft information
        
        Raises:
            TimeoutError: If task doesn't complete within max_wait seconds
            ValueError: If task fails or is not found
        """
        if not profile_id:
            raise ValueError("profile_id is required (set as default or pass as parameter)")
        
        start_time = time.time()
        task_found_in_pending = False
        
        if verbose:
            print(f"Starting to poll task {task_id}...")
        
        while time.time() - start_time < max_wait:
            try:
                pending_tasks_data = self.get_pending_tasks(profile_id)
                pending_tasks = pending_tasks_data.get("pending_tasks", [])
            except requests.HTTPError as e:
                if e.response and (e.response.status_code == 429 or "Rate limit exceeded" in str(e)):
                    if verbose:
                        print(f"⚠ Rate limit hit during polling: {e}")
                        print("Waiting before retrying...")
                    # Wait a bit longer before retrying
                    time.sleep(min(poll_interval * 2, 60))
                    continue
                raise
            
            if not isinstance(pending_tasks, list):
                if verbose:
                    print(f"Warning: Unexpected pending tasks format: {pending_tasks}")
                time.sleep(poll_interval)
                continue
            
            task_in_pending = None
            for task in pending_tasks:
                if task.get("id") == task_id:
                    task_in_pending = task
                    print("Task found in pending list")
                    task_found_in_pending = True
                    break
            
            if task_in_pending:
                state = task_in_pending.get("status", "unknown")
                progress_pct = task_in_pending.get('progress_pct')
                
                if progress_pct is not None:
                    progress_str = f" (progress: {progress_pct:.1f}%)"
                else:
                    progress_str = ""
                
                if verbose:
                    print(f"Task {task_id}: {state}{progress_str}")
            else:
                if task_found_in_pending:
                    if verbose:
                        print(f"Task {task_id} no longer in pending list - checking status...")
                else:
                    if verbose:
                        print(f"Task {task_id} not found in pending - checking status...")
                break
            
            time.sleep(poll_interval)
        
        if time.time() - start_time >= max_wait:
            raise TimeoutError(f"Task {task_id} did not complete within {max_wait} seconds")
        
        # Check task status to see if it completed
        if verbose:
            print("Checking task status...")
        
        try:
            status_list = self.get_task_status(task_id, profile_id)
            if status_list:
                task_status = status_list[0]
                status = task_status.get("status", "").lower()
                
                if status == "completed":
                    if verbose:
                        print(f"✓ Task {task_id} completed successfully")
                    # Return the task status which should contain generation info
                    return task_status
                elif status == "failed":
                    error_msg = task_status.get("error_message", "Task failed")
                    raise ValueError(f"Task {task_id} failed: {error_msg}")
                else:
                    # Still processing or unknown status
                    raise ValueError(f"Task {task_id} has unexpected status: {status}")
            else:
                raise ValueError(f"Task {task_id} not found in status endpoint")
        except requests.HTTPError as e:
            if e.response and (e.response.status_code == 429 or "Rate limit exceeded" in str(e)):
                if verbose:
                    print(f"⚠ Rate limit hit when checking status: {e}")
                    print("Waiting a moment before retrying...")
                time.sleep(30)
                status_list = self.get_task_status(task_id, profile_id)
                if status_list:
                    task_status = status_list[0]
                    status = task_status.get("status", "").lower()
                    if status == "completed":
                        return task_status
                    elif status == "failed":
                        error_msg = task_status.get("error_message", "Task failed")
                        raise ValueError(f"Task {task_id} failed: {error_msg}")
            raise
    
    def create_and_wait(
        self,
        prompt: str,
        title: Optional[str] = None,
        orientation: str = "portrait",
        size: str = "small",
        n_frames: int = 300,
        model: str = "sy_8",
        poll_interval: int = 60,
        max_wait: int = 1200,
        verbose: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a video and wait for it to complete.
        
        Convenience method that combines create_video and poll_task_until_complete.
        
        Args:
            prompt: Video generation prompt (required)
            title: Video title (optional)
            orientation: "portrait", "landscape", or "square" (default: "portrait")
            size: "small", "medium", or "large" (default: "small")
            n_frames: Number of frames (default: 300)
            model: Model to use (default: "sy_8")
            poll_interval: Seconds between status checks (default: 60)
            max_wait: Maximum seconds to wait (default: 1200)
            verbose: Whether to print progress messages (default: True)
            **kwargs: Additional parameters for create_video
        
        Returns:
            Dictionary containing completed video information
        
        Raises:
            TimeoutError: If task doesn't complete within max_wait seconds
            ValueError: If task fails
        """
        if verbose:
            print(f"Creating video with prompt: {prompt[:50]}...")
        
        create_result = self.create_video(
            prompt=prompt,
            title=title,
            orientation=orientation,
            size=size,
            n_frames=n_frames,
            model=model,
            **kwargs
        )
        
        task_id = create_result.get("id")
        if not task_id:
            raise ValueError("No task ID in create response")
        
        if verbose:
            print(f"Created task {task_id}, waiting for completion...")
        
        return self.poll_task_until_complete(
            task_id=task_id,
            profile_id=create_result.get("profile_id"),
            poll_interval=poll_interval,
            max_wait=max_wait,
            verbose=verbose
        )


# Example usage
if __name__ == "__main__":
    # Initialize the generator
    generator = SoraVideoGenerator()

    task_id = "task_01kd3cqc5afbhvn6d4vw7xxa9d"
    status = generator.get_task_status(task_id, profile_id="k183j7tb")

    print(status)

    # try:
    #     result = generator.create_and_wait(
    #         prompt="a cat smiling and running in the middle of the living room",
    #         orientation="portrait",
    #         size="small",
    #         verbose=True
    #     )
    #     print("\n✓ Video completed!")
    #     print(f"Task ID: {result.get('id')}")
    #     print(f"Status: {result.get('status')}")
    # except Exception as e:
    #     print(f"\n✗ Error: {e}")
    #
    # # Example 2: Create a video and check status manually
    # try:
    #     create_result = generator.create_video(
    #         prompt="a beautiful sunset over the ocean"
    #     )
    #     task_id = create_result.get("id")
    #     print(f"\nCreated task: {task_id}")
    #
    #     # Check if pending
    #     is_pending = generator.is_task_pending(task_id)
    #     print(f"Is pending: {is_pending}")
    #
    #     # Get status
    #     task_id = "task_01kd3cqc5afbhvn6d4vw7xxa9d"
    #     status = generator.get_task_status(task_id)
    #     print(f"Status: {status}")
    # except Exception as e:
    #     print(f"\n✗ Error: {e}")
