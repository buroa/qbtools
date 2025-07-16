package utils

import (
	"fmt"
	"os"
	"path/filepath"
	"syscall"
	"time"
)

// FormatBytes formats bytes into human readable format
func FormatBytes(bytes int64) string {
	const unit = 1024
	if bytes < unit {
		return fmt.Sprintf("%d B", bytes)
	}
	div, exp := int64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.2f %ciB", float64(bytes)/float64(div), "KMGTPE"[exp])
}

func SecondsFromDays(days float64) int64 {
	return int64(days * 24 * 60 * 60)
}

func DaysFromSeconds(seconds int64) float64 {
	return float64(seconds) / (24 * 60 * 60)
}

func DHMS(totalSeconds int64) string {
	seconds := totalSeconds % 60
	totalMinutes := totalSeconds / 60
	totalHours := totalMinutes / 60
	minutes := totalMinutes % 60
	days := totalHours / 24
	hours := totalHours % 24
	return fmt.Sprintf("%dd%dh%dm%ds", days, hours, minutes, seconds)
}

// IsLinked checks if a file or directory has hardlinks or symlinks
func IsLinked(path string) bool {
	if isSymlink(path) {
		return true
	}
	return isHardLinked(path)
}

func isSymlink(path string) bool {
	info, err := os.Lstat(path)
	if err != nil {
		return false
	}
	return info.Mode()&os.ModeSymlink != 0
}

func isHardLinked(path string) bool {
	info, err := os.Lstat(path)
	if err != nil {
		return false
	}

	if info.Mode().IsRegular() {
		stat, ok := info.Sys().(*syscall.Stat_t)
		if !ok {
			return false
		}
		return stat.Nlink > 1
	}

	if info.IsDir() {
		hasLinkedFile := false
		filepath.Walk(path, func(filePath string, fileInfo os.FileInfo, err error) error {
			if err != nil {
				return nil
			}
			if fileInfo.Mode().IsRegular() {
				if stat, ok := fileInfo.Sys().(*syscall.Stat_t); ok && stat.Nlink > 1 {
					hasLinkedFile = true
					return filepath.SkipDir
				}
				if isSymlink(filePath) {
					hasLinkedFile = true
					return filepath.SkipDir
				}
			}
			return nil
		})
		return hasLinkedFile
	}

	return false
}

// CalculateDateTags calculates date-based tags based on time difference
func CalculateDateTags(prefix string, timestamp int64, now time.Time) string {
	diff := now.Sub(time.Unix(timestamp, 0))
	days := int(diff.Hours() / 24)

	if days == 0 {
		return fmt.Sprintf("%s:1d", prefix)
	} else if days <= 7 {
		return fmt.Sprintf("%s:7d", prefix)
	} else if days <= 30 {
		return fmt.Sprintf("%s:30d", prefix)
	} else if days <= 180 {
		return fmt.Sprintf("%s:180d", prefix)
	} else {
		return fmt.Sprintf("%s:>180d", prefix)
	}
}

func StringSet(slice []string) map[string]struct{} {
	set := make(map[string]struct{})
	for _, s := range slice {
		set[s] = struct{}{}
	}
	return set
}

func AreSetsEqual(a, b []string) bool {
	setA := StringSet(a)
	setB := StringSet(b)

	if len(setA) != len(setB) {
		return false
	}

	for k := range setA {
		if _, ok := setB[k]; !ok {
			return false
		}
	}

	return true
}
