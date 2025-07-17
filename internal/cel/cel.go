package cel

import (
	"fmt"
	"net/url"
	"strings"
	"time"

	"github.com/autobrr/go-qbittorrent"
	"github.com/google/cel-go/cel"
	"github.com/google/cel-go/common/types"
	"github.com/google/cel-go/common/types/ref"
	"github.com/google/cel-go/common/types/traits"
	"github.com/google/cel-go/ext"
	"golang.org/x/net/publicsuffix"
)

// TorrentContext represents the context available to CEL expressions
type TorrentContext struct {
	// Basic torrent information
	Hash        string
	Name        string
	Size        int64
	Progress    float64
	State       string
	Category    string
	Tags        string
	SavePath    string
	ContentPath string

	// Tracker information
	Tracker         string
	TrackerName     string
	TrackerDomain   string
	TrackerStatus   string
	TrackerMessages []string

	// Timing information
	AddedOn      int64
	CompletedOn  int64
	LastActivity int64
	SeedingTime  int64

	// Ratio and transfer information
	Ratio      float64
	Downloaded int64
	Uploaded   int64

	// Calculated fields
	SeedDays     float64
	AgeDays      float64
	ActivityDays float64
}

// CELEnvironment manages CEL expressions and evaluation
type CELEnvironment struct {
	env *cel.Env
}

// NewCELEnvironment creates a new CEL environment with torrent-specific functions
func NewCELEnvironment() (*CELEnvironment, error) {
	env, err := cel.NewEnv(
		// Declare all torrent fields as variables
		cel.Variable("Hash", cel.StringType),
		cel.Variable("Name", cel.StringType),
		cel.Variable("Size", cel.IntType),
		cel.Variable("Progress", cel.DoubleType),
		cel.Variable("State", cel.StringType),
		cel.Variable("Category", cel.StringType),
		cel.Variable("Tags", cel.StringType),
		cel.Variable("SavePath", cel.StringType),
		cel.Variable("ContentPath", cel.StringType),
		cel.Variable("Tracker", cel.StringType),
		cel.Variable("TrackerName", cel.StringType),
		cel.Variable("TrackerDomain", cel.StringType),
		cel.Variable("TrackerStatus", cel.StringType),
		cel.Variable("TrackerMessages", cel.ListType(cel.StringType)),
		cel.Variable("AddedOn", cel.IntType),
		cel.Variable("CompletedOn", cel.IntType),
		cel.Variable("LastActivity", cel.IntType),
		cel.Variable("SeedingTime", cel.IntType),
		cel.Variable("Ratio", cel.DoubleType),
		cel.Variable("Downloaded", cel.IntType),
		cel.Variable("Uploaded", cel.IntType),
		cel.Variable("SeedDays", cel.DoubleType),
		cel.Variable("AgeDays", cel.DoubleType),
		cel.Variable("ActivityDays", cel.DoubleType),
		ext.Strings(),
		ext.Math(),

		// Custom functions
		cel.Function("seedDays",
			cel.MemberOverload("torrent_seed_days", []*cel.Type{cel.IntType}, cel.DoubleType,
				cel.UnaryBinding(func(value ref.Val) ref.Val {
					seconds := value.(types.Int)
					days := float64(seconds) / (24 * 60 * 60)
					return types.Double(days)
				}),
			),
		),

		cel.Function("ageDays",
			cel.MemberOverload("torrent_age_days", []*cel.Type{cel.IntType}, cel.DoubleType,
				cel.UnaryBinding(func(value ref.Val) ref.Val {
					timestamp := value.(types.Int)
					if timestamp == 0 {
						return types.Double(0)
					}
					age := time.Since(time.Unix(int64(timestamp), 0))
					days := age.Hours() / 24
					return types.Double(days)
				}),
			),
		),

		cel.Function("activityDays",
			cel.MemberOverload("torrent_activity_days", []*cel.Type{cel.IntType}, cel.DoubleType,
				cel.UnaryBinding(func(value ref.Val) ref.Val {
					timestamp := value.(types.Int)
					if timestamp == 0 {
						return types.Double(0)
					}
					age := time.Since(time.Unix(int64(timestamp), 0))
					days := age.Hours() / 24
					return types.Double(days)
				}),
			),
		),

		cel.Function("contains",
			cel.Overload("contains_string_string", []*cel.Type{cel.StringType, cel.StringType}, cel.BoolType,
				cel.BinaryBinding(func(lhs, rhs ref.Val) ref.Val {
					str := lhs.(types.String)
					substr := rhs.(types.String)
					return types.Bool(strings.Contains(string(str), string(substr)))
				}),
			),
		),

		cel.Function("containsAny",
			cel.MemberOverload("string_contains_any", []*cel.Type{cel.ListType(cel.StringType), cel.ListType(cel.StringType)}, cel.BoolType,
				cel.BinaryBinding(func(lhs, rhs ref.Val) ref.Val {
					messages := lhs.(traits.Lister)
					patterns := rhs.(traits.Lister)

					messagesSize := int(messages.Size().(types.Int))
					patternsSize := int(patterns.Size().(types.Int))

					for i := 0; i < messagesSize; i++ {
						msg := messages.Get(types.Int(i)).(types.String)
						msgStr := strings.ToUpper(string(msg))

						for j := 0; j < patternsSize; j++ {
							pattern := patterns.Get(types.Int(j)).(types.String)
							if strings.Contains(msgStr, string(pattern)) {
								return types.True
							}
						}
					}
					return types.False
				}),
			),
		),

		cel.Function("hasTag",
			cel.MemberOverload("torrent_has_tag", []*cel.Type{cel.StringType, cel.StringType}, cel.BoolType,
				cel.BinaryBinding(func(lhs, rhs ref.Val) ref.Val {
					tags := lhs.(types.String)
					tag := rhs.(types.String)
					tagList := strings.Split(string(tags), ",")
					for _, t := range tagList {
						if strings.TrimSpace(t) == string(tag) {
							return types.True
						}
					}
					return types.False
				}),
			),
		),

		cel.Function("trackerDomain",
			cel.MemberOverload("tracker_domain", []*cel.Type{cel.StringType}, cel.StringType,
				cel.UnaryBinding(func(value ref.Val) ref.Val {
					trackerURL := value.(types.String)
					if trackerURL == "" {
						return types.String("")
					}

					parsedURL, err := url.Parse(string(trackerURL))
					if err != nil {
						return types.String("")
					}

					tldPlusOne, err := publicsuffix.EffectiveTLDPlusOne(parsedURL.Hostname())
					if err != nil {
						return types.String("")
					}

					return types.String(strings.ToLower(tldPlusOne))
				}),
			),
		),
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create CEL environment: %w", err)
	}

	return &CELEnvironment{env: env}, nil
}

// CompileExpression compiles a CEL expression
func (c *CELEnvironment) CompileExpression(expression string) (*cel.Ast, error) {
	ast, issues := c.env.Compile(expression)
	if issues != nil && issues.Err() != nil {
		return nil, fmt.Errorf("failed to compile CEL expression '%s': %w", expression, issues.Err())
	}
	return ast, nil
}

// EvaluateExpression evaluates a compiled CEL expression with the given context
func (c *CELEnvironment) EvaluateExpression(ast *cel.Ast, context *TorrentContext) (interface{}, error) {
	prg, err := c.env.Program(ast)
	if err != nil {
		return nil, fmt.Errorf("failed to create CEL program: %w", err)
	}

	result, _, err := prg.Eval(map[string]interface{}{
		"Hash":            context.Hash,
		"Name":            context.Name,
		"Size":            context.Size,
		"Progress":        context.Progress,
		"State":           context.State,
		"Category":        context.Category,
		"Tags":            context.Tags,
		"SavePath":        context.SavePath,
		"ContentPath":     context.ContentPath,
		"Tracker":         context.Tracker,
		"TrackerName":     context.TrackerName,
		"TrackerDomain":   context.TrackerDomain,
		"TrackerStatus":   context.TrackerStatus,
		"TrackerMessages": context.TrackerMessages,
		"AddedOn":         context.AddedOn,
		"CompletedOn":     context.CompletedOn,
		"LastActivity":    context.LastActivity,
		"SeedingTime":     context.SeedingTime,
		"Ratio":           context.Ratio,
		"Downloaded":      context.Downloaded,
		"Uploaded":        context.Uploaded,
		"SeedDays":        context.SeedDays,
		"AgeDays":         context.AgeDays,
		"ActivityDays":    context.ActivityDays,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to evaluate CEL expression: %w", err)
	}

	return result.Value(), nil
}

// CreateTorrentContext creates a TorrentContext from a qBittorrent torrent and tracker config
func CreateTorrentContext(torrent qbittorrent.Torrent, trackerName string) *TorrentContext {
	now := time.Now()

	// Get tracker URL and domain
	tracker := torrent.Tracker
	if tracker == "" && len(torrent.Trackers) > 0 {
		tracker = torrent.Trackers[0].Url
	}

	trackerDomain := ""
	if tracker != "" {
		if parsedURL, err := url.Parse(tracker); err == nil {
			if tldPlusOne, err := publicsuffix.EffectiveTLDPlusOne(parsedURL.Hostname()); err == nil {
				trackerDomain = strings.ToLower(tldPlusOne)
			}
		}
	}

	// Get tracker messages
	var trackerMessages []string
	var trackerStatus string
	for _, tracker := range torrent.Trackers {
		if tracker.Message != "" {
			trackerMessages = append(trackerMessages, strings.ToUpper(tracker.Message))
		}
		if tracker.Status != qbittorrent.TrackerStatusOK {
			trackerStatus = fmt.Sprintf("%d", tracker.Status)
		}
	}

	// Calculate days
	seedDays := float64(torrent.SeedingTime) / (24 * 60 * 60)
	ageDays := 0.0
	activityDays := 0.0

	if torrent.AddedOn > 0 {
		ageDays = now.Sub(time.Unix(torrent.AddedOn, 0)).Hours() / 24
	}

	if torrent.LastActivity > 0 {
		activityDays = now.Sub(time.Unix(torrent.LastActivity, 0)).Hours() / 24
	}

	return &TorrentContext{
		Hash:            torrent.Hash,
		Name:            torrent.Name,
		Size:            torrent.Size,
		Progress:        torrent.Progress,
		State:           string(torrent.State),
		Category:        torrent.Category,
		Tags:            torrent.Tags,
		SavePath:        torrent.SavePath,
		ContentPath:     torrent.ContentPath,
		Tracker:         tracker,
		TrackerName:     trackerName,
		TrackerDomain:   trackerDomain,
		TrackerStatus:   trackerStatus,
		TrackerMessages: trackerMessages,
		AddedOn:         torrent.AddedOn,
		CompletedOn:     torrent.CompletionOn,
		LastActivity:    torrent.LastActivity,
		SeedingTime:     torrent.SeedingTime,
		Ratio:           torrent.Ratio,
		Downloaded:      torrent.Downloaded,
		Uploaded:        torrent.Uploaded,
		SeedDays:        seedDays,
		AgeDays:         ageDays,
		ActivityDays:    activityDays,
	}
}
